from datetime import datetime as dt, timedelta as tmd
import pandas as pd

from PortfolioAnalysis.PortfolioLoader import PortfolioLoader
from PositionAnalysis.OpenedPositionSummary import OpenedPositionSummary
from Functions.TechnicalFunctions import *
from Functions.FileCommunication import *
from Functions.TimeFunctions import now
from Functions.Items import period_dict, currencies

class PositionManipulator:
    """Klasa ładuje portfel (otwarty bądź dopiero rekomendację) zapisany w pliku
    i pozwala na przeliczenie wartości portfela dla danej kwoty PLN. Posiada również funkcjonalność
    otwarcia pozycji, czyli zapisania portfela do otwartych pozycji, jeśli był on rekomendacją.
    """
    def __init__(self,
                 info: dict,
                 filename_load: str,
                 filepath_load: str):
        
        self.info = info
        
        self.statDict = LoadDict(filename_load, filepath_load)
        self.portfolio = self.statDict['SkładPortfela']
        self.symbols = self.portfolio.keys()
        
    def Recalculate(self, K: float):
        print(f"Skład portfela przeliczony dla kwoty {K} PLN:")
        for key, val in self.portfolio.items():
            print(f"\t{key}: {K*val/100 :.2f} PLN")
    
    # Do tej funkcji trzeba dodać możliwość zapisania kluczowych statystyk pozycji, takich jak
    # cena otwarcia, wartość w PLN, kursy walutowe w chwili otwarcia, czas otwarcia itp
    def OpenPosition(self, K: float, filename_save: str):
        
        currencies = getCurrencies(info=self.info)
        
        open_prices = {}
        for symbol in self.symbols:
            open_prices[symbol] = getSymbol(symbol, just_now=True) + self.info[symbol]['SpreadAbs']
            
        self.statDict['KursySymboliOtwarcia'] = open_prices
        self.statDict['KursyWalutoweOtwarcia'] = currencies
        
        symbol_currencies = {}
        for symbol in self.symbols:
            symbol_currencies[symbol] = self.info[symbol]['Waluta']
        
        self.statDict['WalutySymboli'] = symbol_currencies
        self.statDict['CzasOtwarciaPozycji'] = now(False)
        self.statDict['Rodzaj'] = 'Otwarta pozycja'
        self.statDict['KwotaInwestycji'] = K
        
        SaveDict(self.statDict, filename_save, 'Positions')
    
    # Poniższą funkcję trzeba przepisać, żeby nie korzystała z API
    # tylko z jakiegoś zapisanego pliku zawierającego dane o obecnie otwartych pozycjach    
    def AnalyzePosition(self):
        return OpenedPositionSummary(statDict = self.statDict, info = self.info)
        
        