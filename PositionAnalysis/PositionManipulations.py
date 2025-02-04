from datetime import datetime as dt, timedelta as tmd
import pandas as pd
import APICommunication.config as cfg
from APICommunication.xAPIConnector import *

from Functions.TechnicalFunctions import XTB_to_pandas
from Functions.TimeFunctions import str_to_UNIX
from Functions.Items import period_dict, currencies

class PositionManipulator:
    
    def __init__(self, statDict, mode: str):

        self.mode = mode.lower()
        assert self.mode in ['open', 'close']
        
    def OpenPosition(self):
        pass
    
    def getCurrencies(self, margin=0.005):
        
        client = APIClient()
        client.execute(loginCommand(cfg.user_id, cfg.pwd))
        
        # wgrywamy kurs walutowy w chwili obecnej
        dt_start = dt.now() + tmd(days=-2)
        dt_end = dt.now()
        
        start, end = dt_start.strftime("%Y-%m-%d %H:%M"), dt_end.strftime("%Y-%m-%d %H:%M")
        startUNIXTIME, endUNIXTIME = str_to_UNIX(start+':00'), str_to_UNIX(end+':00')

        currency_prices = {}
        for currency_symbol in currencies:
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

            currency_now = currency_bid.iloc[-1]*(1.0+margin)
            currency_prices[currency_symbol] = currency_now
        
        return currency_prices
        
        