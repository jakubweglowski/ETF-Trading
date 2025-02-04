from datetime import datetime as dt, timedelta as tmd
import pandas as pd

from APICommunication.xAPIConnector import *

from PortfolioAnalysis.PortfolioLoader import PortfolioLoader
from PositionAnalysis.PositionAnalyzer import PositionAnalyzer
from Functions.TechnicalFunctions import XTB_to_pandas
from Functions.FileCommunication import SaveDict
from Functions.TimeFunctions import str_to_UNIX, now
from Functions.Items import period_dict, currencies

class PositionManipulator:
    
    def __init__(self, 
                 user_id: str, 
                 pwd: str, 
                 info: dict,
                 filename_load: str,
                 filepath_load: str):
        
        self.user_id = user_id
        self.pwd = pwd
        
        self.info = info
        self.client = None
        
        pl = PortfolioLoader(filename_load, filepath_load)
        self.statDict = pl.statDict
        self.portfolio = pl.portfolio
        
    def connect(self, verbose: bool = True):    
        self.client = APIClient()
        if verbose: print(f"\t[{now(False)}] Loguję do API...")
        self.client.execute(loginCommand(self.user_id, self.pwd))
    
    def disconnect(self, verbose: bool = True):
        if verbose: print(f"\t[{now(False)}] Wylogowuję z API...")
        self.client.disconnect()
        
    def get_currencies(self, margin=0.005):
        
        # wgrywamy kurs walutowy w chwili obecnej
        dt_start = dt.now() + tmd(days=-2)
        dt_end = dt.now()
        
        start, end = dt_start.strftime("%Y-%m-%d %H:%M"), dt_end.strftime("%Y-%m-%d %H:%M")
        startUNIXTIME, endUNIXTIME = str_to_UNIX(start+':00'), str_to_UNIX(end+':00')

        currency_prices = {'bid': {}, 'ask': {}}
        
        self.connect(False)
        for currency_symbol in currencies:
            args = {'info': {
                            'end': endUNIXTIME,
                            'start': startUNIXTIME,
                            'symbol': currency_symbol,
                            'period': period_dict['1min']
            }}
            response = self.client.commandExecute('getChartRangeRequest', arguments=args)

            try:
                currency_bid = XTB_to_pandas(response)
            except:
                print(f"[BŁĄD] Błąd pobierania danych z API: nie można pobrać aktualnego kursu walutowego.")
                currency_bid = pd.Series({0: pd.NA})

            currency_prices['bid'][currency_symbol] = currency_bid.iloc[-1]*(1.0-margin)
            
            currency_spread = self.info[currency_symbol]['SpreadProc']
            currency_prices['ask'][currency_symbol] = currency_bid.iloc[-1]*(1+currency_spread)*(1.0+margin)
        
        self.disconnect(False)
        return currency_prices
    
    def Recalculate(self, K: float):
        print(f"Skład portfela przeliczony dla kwoty {K} PLN:")
        for key, val in self.statDict['SkładPortfela'].items():
            print(f"\t{key}: {K*val/100 :.2f} PLN")
    
    def OpenPosition(self, filename_save: str):
        
        currencies = self.get_currencies()
        self.statDict['KursyWalutoweOtwarcia'] = currencies
        self.statDict['CzasOtwarcia'] = now(False)
        
        SaveDict(self.statDict, filename_save, 'Positions')
        
    def AnalyzePosition(self, omit_symbols: list = ['COSMOS']):
                
        self.connect(False)
        args = {
            "openedOnly": True
        }
        response = self.client.commandExecute('getTrades', args)
        if response['status'] == False:
            self.disconnect(False)
            raise Warning(f"[BŁĄD: {now(False)}] Błąd wysyłania zapytania do API: {response['errorDescr']}")
        else:
            currentTrades = {x['symbol']:
                        {'CenaOtwarcia': x['open_price'], 
                        'CenaAktualna': x['close_price'],
                        'WartoscPoczatkowaPLN': x['nominalValue'],
                        'CzasOtwarcia': dt.fromtimestamp(x['open_time']/1000).strftime("%Y-%m-%d %H:%M:%S")
                        }
                    for x in response['returnData'] if x['symbol'] not in omit_symbols}
            
            self.disconnect(False)
            
            try:
                exchange_rates_open = self.statDict['KursyWalutoweOtwarcia']
            except KeyError:
                print("[OSTRZEŻENIE] W pliku nie zapisano kursów walutowych w chwili otwarcia pozycji.")
                exchange_rates_open = None
                
            return PositionAnalyzer(currentTrades, 
                                    self.info, 
                                    self.portfolio, 
                                    exchange_rates_open=exchange_rates_open)
        
        