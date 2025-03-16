from datetime import datetime as dt, timedelta as tmd
import pandas as pd

from PortfolioAnalysis.PortfolioLoader import PortfolioLoader
from PositionAnalysis.OpenedPositionSummary import OpenedPositionSummary
from Functions.TechnicalFunctions import *
from Functions.FileCommunication import SaveDict
from Functions.TimeFunctions import str_to_UNIX, now
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
        
        pl = PortfolioLoader(filename_load, filepath_load)
        self.statDict = pl.statDict
        self.portfolio = pl.portfolio
    
    def Recalculate(self, K: float):
        print(f"Skład portfela przeliczony dla kwoty {K} PLN:")
        for key, val in self.statDict['SkładPortfela'].items():
            print(f"\t{key}: {K*val/100 :.2f} PLN")
    
    # Do tej funkcji trzeba dodać możliwość zapisania kluczowych statystyk pozycji, takich jak
    # cena otwarcia, wartość w PLN, kursy walutowe w chwili otwarcia, czas otwarcia itp
    def OpenPosition(self, filename_save: str):
        
        currencies = getCurrencies(info=self.info)
        self.statDict['KursyWalutoweOtwarcia'] = currencies
        self.statDict['CzasOtwarcia'] = now(False)
        
        SaveDict(self.statDict, filename_save, 'Positions')
    
    # Poniższą funkcję trzeba przepisać, żeby nie korzystała z API
    # tylko z jakiegoś zapisanego pliku zawierającego dane o obecnie otwartych pozycjach    
    def AnalyzePosition(self, omit_symbols: list = ['COSMOS']):
                
        self.connect(False)
        args = {
            "openedOnly": True
        }
        response = self.client.commandExecute('getTrades', args)
        if response['status'] == False:
            self.disconnect(False)
            raise Warning(f"[BŁĄD: {now(False)}] Błąd wysyłania zapytania do API: {response['errorDescr']}")
        else:
            currentTrades = {x['symbol']:
                        {'CenaOtwarcia': x['open_price'], 
                        'CenaAktualna': x['close_price'],
                        'WartoscPoczatkowaPLN': x['nominalValue'],
                        'CzasOtwarcia': dt.fromtimestamp(x['open_time']/1000).strftime("%Y-%m-%d %H:%M:%S")
                        }
                    for x in response['returnData'] if x['symbol'] not in omit_symbols}
            
            self.disconnect(False)
            
            try:
                exchange_rates_open = self.statDict['KursyWalutoweOtwarcia']
            except KeyError:
                print("[OSTRZEŻENIE] W pliku nie zapisano kursów walutowych w chwili otwarcia pozycji.")
                exchange_rates_open = None
                
            return OpenedPositionSummary(currentTrades, 
                                         self.info, 
                                         self.portfolio, 
                                         exchange_rates_open=exchange_rates_open)
        
        