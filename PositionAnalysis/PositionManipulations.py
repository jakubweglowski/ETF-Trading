from datetime import datetime as dt
import pandas as pd
from IPython.display import display

from Functions.TechnicalFunctions import *
from Functions.FileCommunication import *
from Functions.TimeFunctions import now
from Functions.Items import currencies

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
            open_prices[symbol] = getSymbol()(symbol, just_now=True) + self.info[symbol]['SpreadAbs']
            
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
        
        
################################################################################################
class OpenedPositionSummary:
    
    def __init__(self,
                 statDict: dict,
                 info: dict):
        
        self.statDict = statDict
        self.portfolio = self.statDict['SkładPortfela']
        self.symbols = self.portfolio.keys()
        self.info = {key: val
                     for key, val in info.items()
                     if key in self.symbols or key in currencies}
        
    def getSummary(self):
        
        K = self.statDict['KwotaInwestycji']
        
        CurrenciesSummary = generateCurrenciesSummary(self.statDict['KursyWalutoweOtwarcia'], self.info)
        
        MainSummary = generateMainSummary(K,
                                          self.portfolio,
                                          self.symbols,
                                          self.statDict['WalutySymboli'],
                                          self.statDict['KursySymboliOtwarcia'],
                                          CurrenciesSummary['Początkowy kurs walutowy (Ask)'],
                                          CurrenciesSummary['Obecny kurs walutowy (Bid)'])
        
        # MainSummary = pd.DataFrame()
        
        # current_prices = {}
        # for symbol in self.symbols:
        #     current_prices[symbol] = getSymbol()(symbol, just_now=True)
            
        # K = self.statDict['KwotaInwestycji']
        # MainSummary['Waluta bazowa'] = {symbol: self.statDict['WalutySymboli'][symbol] for symbol in self.symbols}
        # MainSummary['Waga w portfelu [%]'] = self.portfolio
        # MainSummary['Wartość początkowa [PLN]'] = K * MainSummary['Waga w portfelu [%]']/100
        
        # MainSummary['Kurs początkowy'] = self.statDict['KursySymboliOtwarcia']
        # MainSummary['Kurs obecny'] = current_prices
        # MainSummary['Stopa zwrotu [%]'] = (MainSummary['Kurs obecny']/MainSummary['Kurs początkowy'] - 1)*100
        
        # open_currencies = self.statDict['KursyWalutoweOtwarcia']['ask']
        # current_currencies = getCurrencies(self.info)['bid']
        
        # MainSummary['Kurs początkowy [PLN]'] = MainSummary['Kurs początkowy'] * MainSummary['Waluta bazowa'].apply(lambda x: open_currencies[x+'PLN'])
        # MainSummary['Kurs obecny [PLN]'] = MainSummary['Kurs obecny'] * MainSummary['Waluta bazowa'].apply(lambda x: current_currencies[x+'PLN'])
        # MainSummary['Stopa zwrotu [PLN, %]'] = (MainSummary['Kurs obecny [PLN]']/MainSummary['Kurs początkowy [PLN]'] - 1)*100
        
        #############################################################################################          
        TimeStats = generateTimeStats(self.statDict['OkresInwestycji'], self.statDict['CzasOtwarciaPozycji'])
        display(TimeStats)
        
        #############################################################################################
        display(CurrenciesSummary)
        
        #############################################################################################
        display(MainSummary.round(4))
        
        #############################################################################################
        ReturnStats = generateReturnStats(K=K, 
                                          portfolioExpectedReturn=self.statDict['OczekiwanyZwrotPortfela'], 
                                          portfolioReturnCI=self.statDict["PrzedziałUfnościZwrotuPortfela"], 
                                          levelCI=self.statDict["PoziomUfności"], 
                                          returns=MainSummary['Stopa zwrotu [%]'], 
                                          returnsPLN=MainSummary['Stopa zwrotu [PLN, %]'], 
                                          weights=MainSummary['Waga w portfelu [%]'])
        display(ReturnStats)
        
        