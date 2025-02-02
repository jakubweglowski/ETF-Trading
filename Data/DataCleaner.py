import pandas as pd
from datetime import datetime as dt, timedelta as tmd
from importlib import reload

import Functions.FileCommunication
reload(Functions.FileCommunication)
from Functions.FileCommunication import *

import Functions.TechnicalFunctions
reload(Functions.TechnicalFunctions)
from Functions.TechnicalFunctions import *

import Functions.StatisticalFunctions
reload(Functions.StatisticalFunctions)
from Functions.StatisticalFunctions import *

import Functions.TimeFunctions
reload(Functions.TimeFunctions)
from Functions.TimeFunctions import *

from Functions.Items import *

class DataCleaner:
    
    def __init__(self, 
                 data: pd.DataFrame, 
                 info: dict,
                 load_only: list = [],
                 propagate: list = [],
                 threshold_TER: float = 0.4,
                 threshold_spreads: float = 0.08,
                 multiplier_NA: float = 1.35,
                 method_volatility: str = 'iqr',
                 measure_volatility: str = 'pct',
                 compare_volatility: str | list[str] = "ema_2w",
                 quantile_volatility: float = 0.075,
                 alpha_EMA: float = 0.1):
        
        if len(load_only) > 0:
            self.load_only = [x for x in load_only if x in list(data.columns)]
            self.load_only.extend(currencies)
            
            self.data = data.loc[:, self.load_only]
            self.info = {key: val for key, val in info.items() if key in self.load_only}
        else:
            self.data = data
            self.info = info
                    
        self.propagate = propagate
        self.spread_df = pd.DataFrame({key: {
            'spreadAbs': val['SpreadAbs'], 
            'spreadProc': val['SpreadProc']
            }
            for key, val in self.info.items() if key in self.data.columns})
        
        self.data = self.data.reindex(sorted(self.data.columns), axis=1)
        self.spread_df = self.spread_df.reindex(sorted(self.spread_df.columns), axis=1)
        
        weekdays = list(~pd.Series(self.data.index).apply(lambda x: x.weekday()).isin([5, 6]))
        self.data = self.data.loc[weekdays, :]
        
        if len(load_only) == 0:
            self._remove_high_TER(threshold_TER)
            self._remove_high_spreads(threshold_spreads)
            self._remove_too_much_NA(multiplier_NA)
            
            self.data = self.data.ffill().bfill()
            self._remove_high_volatility(method_volatility,
                                         measure_volatility,
                                         compare_volatility,
                                         quantile_volatility,
                                         alpha_EMA)
        
        self.data = self.data.dropna()
        
        assert set(self.data.columns) == set(self.spread_df.columns), f"[BŁĄD] Wystąpił nieoczekiwany błąd."
        assert all([x in list(self.data.columns) for x in currencies]), f"[BŁĄD] Brakuje danych o kursach walut."
         
    def updateData(self, 
                   symbols: list[str], 
                   method: str = 'loc'):
        print(f"\tAktualizacja danych...")
        method = method.lower()
        assert method in ['loc', 'drop'], "[BŁĄD] Argument 'method' musi być jednym z 'loc', 'drop'."
        valid_symbols = [x for x in symbols if x in self.data.columns]
        
        if method == 'loc':
            for x in self.propagate:
                if x not in valid_symbols: valid_symbols.append(x)
            print(f"\tPozostawiam {len(valid_symbols)} instrumentów.")
            self.data = self.data.loc[:, valid_symbols] 
        if method == 'drop': 
            for x in self.propagate:
                if x in valid_symbols: valid_symbols.remove(x)
            print(f"\tPozostawiam {len(self.data.columns) - len(valid_symbols)} instrumentów.")
            self.data = self.data.drop(columns=valid_symbols)
        
        assert all([x in self.spread_df.columns for x in self.data.columns]), "[BŁĄD] Istnieje ticker, dla którego pobrano dane, ale nie pobrano spreadu."
        
        self.spread_df = self.spread_df.loc[:, self.data.columns]

        
    def _remove_too_much_NA(self, multiplier: float = 1.30):
        assert multiplier >= 1, f'[BŁĄD: {now(False)}] Mnożnik musi wynosić co najmniej 1.'
        ndays = len(self.data.index)
        max_na = int(ndays * (1/6) * multiplier) + 1
        symbols = list(self.data.columns[self.data.isna().sum() <= max_na])
        for x in currencies:
            if x not in symbols: symbols.append(x)
        print("[INFO] Usuwanie instrumentów o dużych brakach w danych.")
        self.updateData(symbols, 'loc')
        # self.data = self.data.loc[:, self.data.isna().sum() < max_na]
        # self.spread_df = self.spread_df.loc[:, self.data.columns]
    
    def _remove_high_spreads(self, threshold: float = 0.1):
        low_spread_proc = self.spread_df.loc['spreadProc', :] < threshold
        symbols = list(self.spread_df.columns[low_spread_proc])
        for x in currencies:
            if x not in symbols: symbols.append(x)
        print("[INFO] Usuwanie instrumentów o wysokich spreadach.")
        self.updateData(symbols, 'loc')
    
    # metody odrzucania 'quantile' i 'mean' powinny być używane z miarą zmienności 'abs'
    # metody odrzucania 'sd' i 'iqr' powinny być używane z miarami zmienności 'pct' i 'exp'
    def _remove_high_volatility(self,
                                method_volatility: str,
                                measure_volatility: str, 
                                compare: str | list[str],
                                quantile: float = 0.05,
                                alpha: float = 0.1):
        method_volatility = method_volatility.lower()
        assert method_volatility in ['quantile', 'mean', 'sd', 'iqr'], '[BŁĄD] Niepoprawna metoda podana do odrzucania instrumentów o dużej zmienności.'
        
        measure_volatility = measure_volatility.lower()
        assert measure_volatility in possible_volatility_measures, "[BŁĄD] Podana miara zmienności nie jest zaimplementowana."
       
        # weryfikacja w duchu komentarzy powyżej
        if method_volatility in ['quantile', 'mean'] and measure_volatility != 'abs':
            print(f"[OSTRZEŻENIE] Metoda odrzucania '{method_volatility}' powinna być używana z miarą zmienności 'abs'. Zmieniam miarę zmienności na 'abs' i kontynuuję...")
            measure_volatility = 'abs'
        if method_volatility in ['sd', 'iqr'] and measure_volatility not in ['pct', 'exp']:
            print(f"[OSTRZEŻENIE] Metoda odrzucania '{method_volatility}' powinna być używana z miarą zmienności 'pct' albo 'exp'. Zmieniam miarę zmienności na 'pct' i kontynuuję...")
            measure_volatility = 'pct'
            
        assert isinstance(compare, str) or isinstance(compare, list), "Argument 'compare' musi być typu 'str' albo 'list[str]'."
        if isinstance(compare, str):
            method, window = decode_compare(compare)

            data_smoothed = Smoothen(self.data, window, method, alpha).dropna()
            data_volatility = Volatility(self.data, data_smoothed, measure_volatility)
            
        else:
            assert len(compare) == 2, "Argument 'compare' musi zawierać dwie metody do porównania."
            method1, window1 = decode_compare(compare[0])
            method2, window2 = decode_compare(compare[1])
            assert window2 > window1, "Okno drugie powinno być dłuższe niż pierwsze."
            
            data_smoothed1 = Smoothen(self.data, window1, method1, alpha).dropna()
            data_smoothed2 = Smoothen(self.data, window2, method2, alpha).dropna()
            data_volatility = Volatility(data_smoothed1, data_smoothed2, measure_volatility)
        
        if method_volatility == 'quantile': volatility = data_volatility.apply(lambda x: getQuantiles(x)[1]).sort_values()
        elif method_volatility == 'mean': volatility = data_volatility.apply(lambda x: x.mean()).sort_values()
        elif method_volatility == 'sd': volatility = data_volatility.apply(lambda x: x.std()).sort_values()
        elif method_volatility == 'iqr': volatility = data_volatility.apply(lambda x: getQuantiles(x)[1]-getQuantiles(x)[0]).sort_values()
        
        symbols = list(getQuantiles(y=volatility, q=quantile, one_sided=True, type_='values').index)
        for x in currencies:
            if x not in symbols: symbols.append(x)
        print("[INFO] Usuwanie instrumentów na podstawie ich zmienności.")
        self.updateData(symbols, 'loc')
    
    def _remove_high_TER(self, threshold: float):
        TER = pd.Series(LoadDict('InstrumentsTER'))
        symbols = list(TER.iloc[(TER < threshold).values].index)
        for x in currencies:
            if x not in symbols: symbols.append(x)
        print("[INFO] Usuwanie instrumentów o wysokich kosztach obsługi.")
        self.updateData(symbols, 'loc')
    
    def getSpreads(self):
        return self.spread_df
        
    def getBidPrice(self):
        return self.data
    
    def getAskPrice(self):
        spread = self.getSpreads().loc['spreadProc']
        data_ask = self.getBidPrice()*(1+spread)
        return data_ask
    
    def getPLNPrices(self):
        trueBid = pd.DataFrame()
        bid = self.getBidPrice()
        for symbol in bid.columns:
            for x in currencies:
                if self.info[symbol]['Waluta'] == x[:3]:
                    trueBid.loc[:, symbol] = bid.loc[:, symbol] * bid.loc[:, x] * 0.995
            
        trueAsk = pd.DataFrame()
        ask = self.getAskPrice()
        for symbol in ask.columns:
            for x in currencies:
                if self.info[symbol]['Waluta'] == x[:3]:
                    trueAsk.loc[:, symbol] = ask.loc[:, symbol] * ask.loc[:, x] * 1.005
        try:
            for x in currencies:
                trueBid = trueBid.drop(columns=[x])
                trueAsk = trueAsk.drop(columns=[x])
        except KeyError:
            pass
        
        assert all(trueBid.columns == trueAsk.columns), f"[BŁĄD] Lista instrumentów dla cen 'bid' oraz 'ask' nie jest identyczna."
        assert all(trueBid.index == trueAsk.index), f"[BŁĄD] Zakres dat dla cen 'bid' oraz 'ask' nie jest identyczny."
        return {'bid': trueBid, 'ask': trueAsk}
    
    def getReturnRates(self, freq: str | int):
        assert isinstance(freq, str) or isinstance(freq, int), "[BŁĄD] Argument 'freq' musi być typu 'str' albo 'int'."
        if isinstance(freq, str): k = recalculate_frequency(freq)
        else: k = freq
        PLNPrices = self.getPLNPrices()
        bidPrice, askPrice = PLNPrices['bid'], PLNPrices['ask']
        returnRates = getReturnRates(bidPrice, askPrice, k)
        return returnRates