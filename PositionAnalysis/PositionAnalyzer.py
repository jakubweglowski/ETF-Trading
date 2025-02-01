import pandas as pd
from datetime import datetime as dt, timedelta as tmd
from importlib import reload

import APICommunication.config as cfg
from APICommunication.xAPIConnector import *

import Functions.TimeFunctions
reload(Functions.TimeFunctions)
from Functions.TimeFunctions import *

import Functions.TechnicalFunctions
reload(Functions.TechnicalFunctions)
from Functions.TechnicalFunctions import *

from Functions.Items import *

class PositionAnalyzer:
    def __init__(self, currentTrades, info, weights: dict | None = None):
        self.currentTrades = currentTrades
        self.info = {key: val
                     for key, val in info.items()
                     if key in self.currentTrades.keys()
                     or key in currencies}
        self.weights = weights
        self.summary = None

    def get_currency(self, client, symbol, margin: float = 0.005):
        # wyszukujemy walutę instrumentu
        for x in currencies:
            if self.info[symbol]['Waluta'] == x[:3]:
                currency_symbol = x
                    
        # wgrywamy kurs walutowy w chwili zakupu instrumentu
        dt_start = dt.strptime(self.currentTrades[symbol]['CzasOtwarcia'], "%Y-%m-%d %H:%M:%S") + tmd(hours=-2)
        dt_end = dt.strptime(self.currentTrades[symbol]['CzasOtwarcia'], "%Y-%m-%d %H:%M:%S") + tmd(hours=2)

        start, end = dt_start.strftime("%Y-%m-%d %H:%M:%S"), dt_end.strftime("%Y-%m-%d %H:%M:%S")
        startUNIXTIME, endUNIXTIME = str_to_UNIX(start), str_to_UNIX(end)
        args = {'info': {
                        'end': endUNIXTIME,
                        'start': startUNIXTIME,
                        'symbol': currency_symbol,
                        'period': period_dict['1h']
        }}
        response = client.commandExecute('getChartRangeRequest', arguments=args)
        if response['status'] == False:
            print(f"[BŁĄD] Błąd pobierania danych z API: {response['errorDescr']}")
            return -1
        
        currency_bid = XTB_to_pandas(response)
        currency_spread = self.info[currency_symbol]['SpreadAbs']
        currency_ask = currency_bid + currency_spread

        opening_time = dt.strptime(self.currentTrades[symbol]['CzasOtwarcia'], "%Y-%m-%d %H:%M:%S")
        opening_time = round_to_nearest_hour(opening_time).strftime("%Y-%m-%d %H")+':00:00'
        currency_open = currency_ask.loc[opening_time]*(1.0+margin)
        
        # wgrywamy kurs walutowy w chwili obecnej
        dt_start = dt.now() + tmd(days=-2)
        dt_end = dt.now()
        
        start, end = dt_start.strftime("%Y-%m-%d %H:%M"), dt_end.strftime("%Y-%m-%d %H:%M")
        startUNIXTIME, endUNIXTIME = str_to_UNIX(start+':00'), str_to_UNIX(end+':00')

        args = {'info': {
                        'end': endUNIXTIME,
                        'start': startUNIXTIME,
                        'symbol': currency_symbol,
                        'period': period_dict['1min']
        }}
        response = client.commandExecute('getChartRangeRequest', arguments=args)
        try:
            currency_bid = XTB_to_pandas(response)
        except:
            print(f"[BŁĄD] Błąd pobierania danych z API: nie można pobrać aktualnego kursu walutowego.")
            currency_bid = pd.Series({0: pd.NA})

        currency_spread = self.info[currency_symbol]['SpreadAbs']
        currency_ask = currency_bid + currency_spread
        currency_now = currency_bid.iloc[-1]*(1.0-margin)
        
        return (currency_open, currency_now)
        
    def getSummary(self):
            
        for symbol in self.currentTrades.keys():
            
            client = APIClient()
            client.execute(loginCommand(cfg.user_id, cfg.pwd))
            
            currency_open, currency_now = self.get_currency(client, symbol)
            self.currentTrades[symbol]['CenaOtwarciaPLN'] = self.currentTrades[symbol]['CenaOtwarcia'] * currency_open
            self.currentTrades[symbol]['CenaAktualnaPLN'] = self.currentTrades[symbol]['CenaAktualna'] * currency_now

            client.disconnect()
        
        self.currentTrades = pd.DataFrame(self.currentTrades)
        
        self.currentTrades.loc['Zwrot [%]', :] = (self.currentTrades.loc['CenaAktualna', :]/self.currentTrades.loc['CenaOtwarcia', :] - 1)*100
        self.currentTrades.loc['ZwrotPLN [%]', :] = (self.currentTrades.loc['CenaAktualnaPLN', :]/self.currentTrades.loc['CenaOtwarciaPLN', :] - 1)*100
        self.currentTrades.loc['Zysk/strata PLN', :] = self.currentTrades.loc['WartoscPoczatkowaPLN', :] * self.currentTrades.loc['ZwrotPLN [%]', :] / 100
        
        self.currentTrades.loc['KursWalutowyOtwarcia'] = self.currentTrades.loc['CenaOtwarciaPLN']/self.currentTrades.loc['CenaOtwarcia']
        self.currentTrades.loc['KursWalutowyAktualny'] = self.currentTrades.loc['CenaAktualnaPLN']/self.currentTrades.loc['CenaAktualna']
        self.currentTrades.loc['ZwrotWalutowy [%]'] = (self.currentTrades.loc['KursWalutowyAktualny']/self.currentTrades.loc['KursWalutowyOtwarcia'] - 1)*100

        self.currentTrades = self.currentTrades.loc[['CzasOtwarcia',
                                                     'CenaOtwarcia', 'CenaAktualna', 'Zwrot [%]',
                                                     'KursWalutowyOtwarcia', 'KursWalutowyAktualny', 'ZwrotWalutowy [%]',
                                                     'CenaOtwarciaPLN', 'CenaAktualnaPLN', 'ZwrotPLN [%]',
                                                     'WartoscPoczatkowaPLN', 'Zysk/strata PLN'], :]
        self.currentTrades.loc['KursWalutowyOtwarcia'] = self.currentTrades.loc['CenaOtwarciaPLN']/self.currentTrades.loc['CenaOtwarcia']
        self.currentTrades.loc['KursWalutowyAktualny'] = self.currentTrades.loc['CenaAktualnaPLN']/self.currentTrades.loc['CenaAktualna']
        return self.currentTrades
    
    def getReturns(self):
        return self.currentTrades.loc['ZwrotPLN [%]', :]
    
    def getProfitLoss(self):
        return self.currentTrades.loc['Zysk/strata PLN', :]
    
    def getPCTReturn(self):
        df = self.getReturns()
        for symbol in df.index:
            df.loc[symbol] *= self.weights[symbol]
        return round(df.sum()/100, 2)
    
    def getPLNReturn(self):
        df = self.getProfitLoss()
        return round(df.sum(), 2)
        