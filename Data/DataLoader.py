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
        # trueSymbols = {} # tu zapisujemy poprawne symbole
        
        beginning_time = time.time()
        n_items = len(symbols)
        for i, symbol in enumerate(symbols):
            
            if verbose and symbol in currencies: print(f"\tPobieram {symbol}")
            # s = alterSymbol(symbol)
                
            if verbose and (i % 300 == 0): 
                print(f"\tPozostało {(1-i/n_items):.0%}.") 
                if i > 0:
                    estimate_time_to_end(i, n_items, beginning_time)         

            # s = reasonProperSymbol(s)
            # if s == '':
            #     print(f"\t[OSTRZEŻENIE] Nie udało się pobrać {symbol}. Zasypiamy na {sleep} sekund... ", end='')
            #     time.sleep(sleep)
            #     print("wstajemy!")
            # else:
            s = (symbol if symbol not in currencies else symbol + '=X')
            try:
                finalData[symbol] = \
                    getSymbol(symbol=s,
                                period=period,
                                start=start,
                                end=end)
                # trueSymbols[symbol] = s 
            except:
                print(f"\t[OSTRZEŻENIE] Nie udało się pobrać {symbol}. Zasypiamy na {sleep} sekund... ", end='')
                time.sleep(sleep)
                print("wstajemy!")
            
        print(f"Zakończono pobieranie")
        
        # # zapisujemy poprawne symbole i kursy (w surowej postaci jako backup)
        # SaveDict(trueSymbols, 'TrueSymbols', 'Data')
        SaveDict(finalData, 'finalData_backup', 'Data/Backup')
        
        return pd.DataFrame(finalData)
    
    
    def loadInstrumentsData(self,
                            start_date: str,
                            end_date: str = now(),
                            filename: str = 'InstrumentsData',
                            filepath: str = 'Data',
                            append: bool = True,
                            verbose: bool = False):
        
        data = LoadData(filename, filepath)
        symbols = list(data.columns)
        
        old_start = data.index[0]
        if start_date < old_start:
            
            print(f"\tPobieramy brakujące dane od {start_date} do {old_start}...")
            
            temp_data = self.getInstrumentsData(symbols=symbols,
                                                start=start_date,
                                                end=shift_date(data.index[0], days=-1),
                                                verbose=verbose)
            new_symbols = [x for x in symbols if x in temp_data.columns]
            
            print(f"\tZagubiliśmy {len(symbols)-len(new_symbols)} instrumentów.")
            
            data = pd.concat([data.loc[:, new_symbols], temp_data.loc[:, new_symbols]])
            symbols = list(data.columns)
            
        old_end = data.index[-1]
        if old_end < end_date:
            
            print(f"\tPobieramy brakujące dane od {old_end} do {end_date}...")
            
            temp_data = self.getInstrumentsData(symbols=symbols, 
                                                start=shift_date(data.index[-1], days=1),
                                                end=end_date,
                                                verbose=verbose)
            new_symbols = [x for x in symbols if x in temp_data.columns]
            
            print(f"\tZagubiliśmy {len(symbols)-len(new_symbols)} instrumentów.")
            
            data = pd.concat([data.loc[:, new_symbols], temp_data.loc[:, new_symbols]])
            
        data.index = unify_time_index(data.index)
        data = data.sort_index()
        
        if append: SaveData(data, filename, filepath)
        
        data = data[(data.index >= start_date) & (data.index <= end_date)]
                
        return data    
    
    def loadInstrumentsInfo(self, filename: str = 'AllInfo', filepath: str = 'Data'):
        return LoadDict(filename, filepath)
            
    