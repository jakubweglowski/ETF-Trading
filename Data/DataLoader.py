import pandas as pd
from datetime import datetime as dt, timedelta as tmd
import time

from APICommunication.xAPIConnector import *

from Functions.FileCommunication import *
from Functions.TimeFunctions import *
from Functions.TechnicalFunctions import *
from PositionAnalysis.OpenedPositionSummary import *
from Functions.Items import *

class DataLoader:
    def __init__(self, user_id, pwd):
        
        self.user_id = user_id
        self.pwd = pwd
        
        self.client = None
        
    def connect(self, verbose: bool = True):    
        self.client = APIClient()
        if verbose: print(f"\t[{now(False)}] Loguję do API...")
        self.client.execute(loginCommand(self.user_id, self.pwd))
    
    def disconnect(self, verbose: bool = True):
        if verbose: print(f"\t[{now(False)}] Wylogowuję z API...")
        self.client.disconnect()
        
    def getInstrumentsData(self,
                symbols: list[str],
                start_date: str,
                end_date: str = now(),
                period: str = '1D',
                reconnect_after: int = 10,
                verbose: bool = False):
        
        for x in currencies:
            if x not in symbols: symbols.append(x)
        
        endUNIXTIME = str_to_UNIX(end_date, full=False)
        start_date = shift_date(start_date, days=-1)
        startUNIXTIME = str_to_UNIX(start_date)
        
        finalData = {}
        connected = False
        
        beginning_time = time.time()
        n_items = len(symbols)
        for i, symbol in enumerate(symbols):
            
            if symbol in currencies: print(f"\tPobieram {symbol}")
            if i % 100 == 0: 
                print(f"\tPozostało {(1-i/n_items):.0%}.") 
                if i > 0:
                    estimate_time_to_end(i, n_items, beginning_time)         
                    
            if i % reconnect_after == 0 or not connected:
                try:
                    self.connect(verbose)
                    connected = True
                except:
                    print(f"\t[BŁĄD: {now(False)}] Błąd połączenia z API przy pobieraniu {symbol}")
                    self.disconnect()
                    connected = False
                    continue            
                
            print(f"\t\t[{(i%reconnect_after) + 1}] Pobieram {symbol}.")
            
            response = getSymbol(symbol=symbol,
                      period=period,
                      start=startUNIXTIME,
                      end=endUNIXTIME,
                      client=self.client)
            try:                    
                finalData[symbol] = XTB_to_pandas(response)
                print("\t\t\t[INFO] Dane zapisane.")
            except:
                print(f"\t\t\t[OSTRZEŻENIE] Nie udało się pobrać {symbol}.")

            if i % reconnect_after == (reconnect_after-1) and connected:
                self.disconnect(verbose)
                time.sleep(18)
                
            time.sleep(2)
            
        print(f"\tZakończono pobieranie")
        if connected: self.disconnect(verbose)
            
        return pd.DataFrame(finalData)
    
    
    def loadInstrumentsData(self,
                            start_date: str,
                            end_date: str = now(),
                            filename: str = 'InstrumentsData',
                            filepath: str = 'Data',
                            append: bool = True,
                            verbose: bool = False):
        
        data = LoadData(filename, filepath).copy()
        data.index = pd.DatetimeIndex(data.index)
        symbols = list(data.columns)
        
        old_start = data.index[0].strftime('%Y-%m-%d')
        if start_date < old_start:
            print(f"\tPobieramy brakujące dane od {start_date} do {old_start}...")
            remaining_data_before = self.getInstrumentsData(symbols, start_date, shift_date(data.index[0].strftime("%Y-%m-%d"), -1).strftime("%Y-%m-%d"), verbose=verbose)
            new_symbols = [x for x in symbols if x in remaining_data_before.columns]
            print(f"\tZagubiliśmy {len(symbols)-len(new_symbols)} instrumentów.")
            data = pd.concat([data.loc[:, new_symbols], remaining_data_before.loc[:, new_symbols]])
            symbols = list(data.columns)
            
        old_end = data.index[-1].strftime('%Y-%m-%d')
        if old_end < end_date:
            print(f"\tPobieramy brakujące dane od {old_end} do {end_date}...")
            remaining_data_after = self.getInstrumentsData(symbols, shift_date(data.index[-1].strftime("%Y-%m-%d"), 1).strftime("%Y-%m-%d"), end_date, verbose=verbose)
            new_symbols = [x for x in symbols if x in remaining_data_after.columns]
            print(f"\tZagubiliśmy {len(symbols)-len(new_symbols)} instrumentów.")
            data = pd.concat([data.loc[:, new_symbols], remaining_data_after.loc[:, new_symbols]])
            
        data = data.sort_index()
        if append: SaveData(data, filename, filepath)
        
        data = data[(data.index >= start_date) & (data.index <= end_date)]
                
        return data
    
    
    def getInstrumentsInfo(self):
        self.connect()
        response = self.client.commandExecute('getAllSymbols')
        if response['status'] == False:
            self.disconnect()
            raise Warning(f"[BŁĄD: {now(False)}] Błąd wysyłania zapytania do API: {response['errorDescr']}")
        else:
            etfs = [x 
                    for x in response['returnData']
                    if (
                            (x['symbol'].find('_5') == -1 and x['categoryName'] == 'ETF')
                            or
                            x['symbol'] in ['EURPLN', 'USDPLN', 'GBPPLN', 'CHFPLN']
                        )
                    ]
            
            info = {x['symbol']:
                        {'Waluta': x['currency'], 
                        'SpreadAbs': x['spreadRaw'],
                        'SpreadProc': round(x['spreadRaw']/x['bid'], 4),
                        'Opis': x['description'],
                        'Typ': x['type']
                        }
                    for x in etfs}
            self.disconnect()
            
            assert all([(x in list(info.keys())) for x in ['EURPLN', 'USDPLN', 'GBPPLN', 'CHFPLN']]), f"[BŁĄD] Nie udało się załadować info dot. przynajmniej jednej z walut niezbędnych do dalszej analizy"
            return info
    
    
    def loadInstrumentsInfo(self, filename: str = 'InstrumentsInfo', filepath: str = 'Data'):
        return LoadDict(filename, filepath)
            
    