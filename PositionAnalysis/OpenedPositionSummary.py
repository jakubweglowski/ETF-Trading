import pandas as pd
from datetime import datetime as dt, timedelta as tmd

import APICommunication.config as cfg
from APICommunication.xAPIConnector import *
from Functions.TimeFunctions import *
from Functions.TechnicalFunctions import *

from Functions.Items import *

class OpenedPositionSummary:
    
    def __init__(self,
                 user_id: str,
                 pwd: str,
                 currentTrades: dict,
                 info: dict,
                 portfolio: dict | None = None, # portfel z wagami
                 exchange_rates_open: dict | None = None):
        
        self.info = {key: val
                     for key, val in info.items()
                     if key in currentTrades.keys()
                     or key in currencies}
        
        self.summary = None
        self.exchange_rates_open = exchange_rates_open
        
        self.portfolio = portfolio
        assert all([x in currentTrades for x in self.portfolio.keys()]), "W portfelu znajduje się instrument, na którym nie ma aktualnie otwartej pozycji."
        self.currentTrades = {key: val
                              for key, val in currentTrades.items() if key in self.portfolio.keys()}

        self.client = None
        self.user_id = user_id
        self.pwd = pwd
        
    def connect(self, verbose: bool = True):    
        self.client = APIClient()
        if verbose: print(f"\t[{now(False)}] Loguję do API...")
        self.client.execute(loginCommand(self.user_id, self.pwd))
    
    def disconnect(self, verbose: bool = True):
        if verbose: print(f"\t[{now(False)}] Wylogowuję z API...")
        self.client.disconnect()
        
    def get_currency(self, symbol: str, margin: float = 0.005):
        
        # wyszukujemy walutę instrumentu
        for x in currencies:
            if self.info[symbol]['Waluta'] == x[:3]:
                currency_symbol = x
                    
        if self.exchange_rates_open is not None:
            currency_open = self.exchange_rates_open['ask'][currency_symbol]
        else:        
            # wgrywamy kurs walutowy w chwili zakupu instrumentu
            start = (dt.strptime(self.currentTrades[symbol]['CzasOtwarcia'], "%Y-%m-%d %H:%M:%S") + tmd(hours=-2)).strftime("%Y-%m-%d %H:%M:%S")
            end = (dt.strptime(self.currentTrades[symbol]['CzasOtwarcia'], "%Y-%m-%d %H:%M:%S") + tmd(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
            
            self.connect(False)
            response = getSymbol(symbol=currency_symbol,
                             period='1h',
                             start=start,
                             end=end,
                             client=self.client)
            self.disconnect(False)
            try:
                currency_bid = XTB_to_pandas(response)
            except:
                print(f"[BŁĄD] Błąd pobierania danych z API: nie można pobrać aktualnego kursu walutowego.")
                print(response)
                currency_bid = pd.Series({0: pd.NA})
                
            currency_spread = self.info[currency_symbol]['SpreadProc']
            currency_ask = currency_bid*(1+currency_spread)

            opening_time = dt.strptime(self.currentTrades[symbol]['CzasOtwarcia'], "%Y-%m-%d %H:%M:%S")
            opening_time = round_to_nearest_hour(opening_time).strftime("%Y-%m-%d %H")+':00:00'
            currency_open = currency_ask.loc[opening_time]*(1.0+margin)
        
        # wgrywamy kurs walutowy w chwili obecnej       
        self.connect(False)
        response = getSymbol(symbol=currency_symbol,
                             client=self.client,
                             just_now=True)
        self.disconnect(False)
        try:
            currency_bid = response['bid']
        except:
            print(f"[BŁĄD] Błąd pobierania danych z API: nie można pobrać aktualnego kursu walutowego.")
            print(response)
            currency_bid = 0.0

        currency_now = currency_bid*(1.0-margin)
                
        return (currency_open, currency_now)
        
    def getSummary(self):
                    
        for symbol in self.currentTrades.keys():
                        
            currency_open, currency_now = self.get_currency(symbol)
            self.currentTrades[symbol]['CenaOtwarciaPLN'] = self.currentTrades[symbol]['CenaOtwarcia'] * currency_open
            self.currentTrades[symbol]['CenaAktualnaPLN'] = self.currentTrades[symbol]['CenaAktualna'] * currency_now
        
        self.currentTrades = pd.DataFrame(self.currentTrades)
        
        self.currentTrades.loc['Zwrot [%]', :] = (self.currentTrades.loc['CenaAktualna', :]/self.currentTrades.loc['CenaOtwarcia', :] - 1)*100
        self.currentTrades.loc['ZwrotPLN [%]', :] = (self.currentTrades.loc['CenaAktualnaPLN', :]/self.currentTrades.loc['CenaOtwarciaPLN', :] - 1)*100
        self.currentTrades.loc['Zysk/strata PLN', :] = self.currentTrades.loc['WartoscPoczatkowaPLN', :] * self.currentTrades.loc['ZwrotPLN [%]', :] / 100
        
        self.currentTrades.loc['KursWalutowyOtwarcia'] = self.currentTrades.loc['CenaOtwarciaPLN']/self.currentTrades.loc['CenaOtwarcia']
        self.currentTrades.loc['KursWalutowyAktualny'] = self.currentTrades.loc['CenaAktualnaPLN']/self.currentTrades.loc['CenaAktualna']
        self.currentTrades.loc['ZwrotWalutowy [%]'] = (self.currentTrades.loc['KursWalutowyAktualny']/self.currentTrades.loc['KursWalutowyOtwarcia'] - 1)*100

        self.currentTrades = self.currentTrades.loc[['CzasOtwarcia', 'WartoscPoczatkowaPLN',
                                                      'CenaOtwarcia', 'CenaAktualna', 'Zwrot [%]',
                                                     'KursWalutowyOtwarcia', 'KursWalutowyAktualny', 'ZwrotWalutowy [%]',
                                                     'CenaOtwarciaPLN', 'CenaAktualnaPLN',
                                                     'ZwrotPLN [%]','Zysk/strata PLN'], :]
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
            df.loc[symbol] *= self.portfolio[symbol]
        return round(df.sum()/100, 2)
    
    def getPLNReturn(self):
        df = self.getProfitLoss()
        return round(df.sum(), 2)
        