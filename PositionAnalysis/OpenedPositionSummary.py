import pandas as pd
from IPython.display import display
from datetime import datetime as dt, timedelta as tmd

from Functions.TimeFunctions import *
from Functions.TechnicalFunctions import *

from Functions.Items import *

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
        
        MainSummary = pd.DataFrame()
        
        current_prices = {}
        for symbol in self.symbols:
            current_prices[symbol] = getSymbol(symbol, just_now=True)
            
        K = self.statDict['KwotaInwestycji']
        MainSummary['Waluta bazowa'] = {symbol: self.statDict['WalutySymboli'][symbol] for symbol in self.symbols}
        MainSummary['Waga w portfelu [%]'] = self.portfolio
        MainSummary['Wartość początkowa [PLN]'] = K * MainSummary['Waga w portfelu [%]']/100
        
        MainSummary['Kurs początkowy'] = self.statDict['KursySymboliOtwarcia']
        MainSummary['Kurs obecny'] = current_prices
        MainSummary['Stopa zwrotu [%]'] = (MainSummary['Kurs obecny']/MainSummary['Kurs początkowy'] - 1)*100
        
        open_currencies = self.statDict['KursyWalutoweOtwarcia']['ask']
        current_currencies = getCurrencies(self.info)['bid']
        
        MainSummary['Kurs początkowy [PLN]'] = MainSummary['Kurs początkowy'] * MainSummary['Waluta bazowa'].apply(lambda x: open_currencies[x+'PLN'])
        MainSummary['Kurs obecny [PLN]'] = MainSummary['Kurs obecny'] * MainSummary['Waluta bazowa'].apply(lambda x: current_currencies[x+'PLN'])
        MainSummary['Stopa zwrotu [PLN, %]'] = (MainSummary['Kurs obecny [PLN]']/MainSummary['Kurs początkowy [PLN]'] - 1)*100
        
        #############################################################################################  
        k = recalculate_frequency(self.statDict['OkresInwestycji'], full=True)
        opening_time = self.statDict['CzasOtwarciaPozycji']
        opening_date = dt.strptime(opening_time, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        TimeStats = pd.DataFrame({'Okres zawarcia pozycji': {'': f'{k} dni'},
                              'Czas otwarcia pozycji': {'': opening_time},
                              'Obecny czas': {'': now(False)},
                              'Przewidywana data zamknięcia pozycji': shift_date(opening_date, k)
                              })
        display(TimeStats)
        
        #############################################################################################
        CurrenciesSummary = pd.DataFrame({'Początkowy kurs walutowy (Ask)': self.statDict['KursyWalutoweOtwarcia']['ask'],
                                          'Obecny kurs walutowy (Bid)': current_currencies})
        CurrenciesSummary['Stopa zwrotu [%]'] = (CurrenciesSummary['Obecny kurs walutowy (Bid)']/CurrenciesSummary['Początkowy kurs walutowy (Ask)'] - 1)*100
        display(CurrenciesSummary.round(4))
        
        #############################################################################################
        display(MainSummary.round(4))
        
        #############################################################################################
        portfolioCI = self.statDict["PrzedziałUfnościZwrotuPortfela"]
        ReturnStats = pd.DataFrame({'Zwrot z portfela [%]': {'': (MainSummary['Stopa zwrotu [%]'] * MainSummary['Waga w portfelu [%]']/100).sum()},
                                    'Zwrot z portfela [PLN, %]': {'': (MainSummary['Stopa zwrotu [PLN, %]'] * MainSummary['Waga w portfelu [%]']/100.).sum()},
                                    'Oczekiwany zwrot z portfela [PLN, %]': {'': self.statDict['OczekiwanyZwrotPortfela']},
                                    f'Przedział ufności ({self.statDict["PoziomUfności"]}) zwrotu portfela [PLN, %]': f'[{portfolioCI["lowCI"]}, {portfolioCI["highCI"]}]'
                                    })
        ReturnStats['Zwrot nominalny [PLN]'] = K * ReturnStats[['Zwrot z portfela [PLN, %]']]/100.
        display(ReturnStats.round(4))
        