import pandas as pd
from datetime import datetime as dt, timedelta as tmd
import time
import yfinance as yf

from Functions.FileCommunication import *
from Functions.TimeFunctions import *
from Functions.TechnicalFunctions import *
from PositionAnalysis.OpenedPositionSummary import *
from Functions.Items import *

class DataLoader:
    
    def __init__(self):
        pass
        
    def getInstrumentsData(self,
                symbols: list[str],
                start: str,
                end: str = now(),
                period: str = '1D',
                verbose: bool = False,
                sleep: int = 10) -> pd.DataFrame:
        
        print(f"\tRozpoczynam pobieranie danych dla {len(symbols)} instrumentów.")
        for x in currencies:
            if x not in symbols: symbols.append(x)
        
        finalData = {} # tu zapisujemy kursy instrumentów
        trueSymbols = {} # tu zapisujemy poprawne symbole
        
        beginning_time = time.time()
        n_items = len(symbols)
        for i, symbol in enumerate(symbols):
            
            if verbose and symbol in currencies: print(f"\tPobieram {symbol}")
            s = alterSymbol(symbol)
                
            if verbose and (i % 100 == 0): 
                print(f"\tPozostało {(1-i/n_items):.0%}.") 
                if i > 0:
                    estimate_time_to_end(i, n_items, beginning_time)         

            s = reasonProperSymbol(s)
            if s == '':
                print(f"\t[OSTRZEŻENIE] Nie udało się pobrać {s}. Zasypiamy na {sleep} sekund...")
                time.sleep(sleep)
            else: 
                finalData[symbol] = \
                    getSymbol(symbol=s,
                              period=period,
                              start=start,
                              end=end)
                trueSymbols[symbol] = s
            
        print(f"Zakończono pobieranie")
        
        # zapisujemy poprawne symbole i kursy (w surowej postaci jako backup)
        SaveDict(trueSymbols, 'TrueSymbols', 'Data')
        SaveDict(finalData, 'finalData_backup', 'Data')
        
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
            remaining_data_before = self.getInstrumentsData(symbols, start_date, shift_date(data.index[0].strftime("%Y-%m-%d"), days=-1), verbose=verbose)
            new_symbols = [x for x in symbols if x in remaining_data_before.columns]
            print(f"\tZagubiliśmy {len(symbols)-len(new_symbols)} instrumentów.")
            data = pd.concat([data.loc[:, new_symbols], remaining_data_before.loc[:, new_symbols]])
            symbols = list(data.columns)
            
        old_end = data.index[-1].strftime('%Y-%m-%d')
        if old_end < end_date:
            print(f"\tPobieramy brakujące dane od {old_end} do {end_date}...")
            remaining_data_after = self.getInstrumentsData(symbols, shift_date(data.index[-1].strftime("%Y-%m-%d"), days=1), end_date, verbose=verbose)
            new_symbols = [x for x in symbols if x in remaining_data_after.columns]
            print(f"\tZagubiliśmy {len(symbols)-len(new_symbols)} instrumentów.")
            data = pd.concat([data.loc[:, new_symbols], remaining_data_after.loc[:, new_symbols]])
            
        data = data.sort_index()
        data.index = data.index.strftime('%Y-%m-%d')
        
        if append: SaveData(data, filename, filepath)
        
        data = data[(data.index >= start_date) & (data.index <= end_date)]
                
        return data    
    
    def loadInstrumentsInfo(self, filename: str = 'InstrumentsInfo', filepath: str = 'Data'):
        return LoadDict(filename, filepath)
            
    