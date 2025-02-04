import pandas as pd
from PortfolioAnalysis.PortfolioPerformance import *
from Functions.FileCommunication import *
from Functions.TimeFunctions import *
from Functions.StatisticalFunctions import *
from Functions.TechnicalFunctions import *

class PortfolioLoader:
    """
    Klasa służąca ładowaniu portfela z zapisanego pliku
    """
    def __init__(self,
                 filename: str,
                 filepath: str = 'Positions'):
        self.statDict = LoadDict(filename, filepath)
        
        self.portfolio = self.statDict['SkładPortfela']
        self.symbols = list(self.portfolio.keys())
        self.freq = self.statDict['OkresInwestycji']
        self.model = self.statDict['Model']
        self.risk_method = self.statDict['MetodaEstymacjiRyzyka']
        
        self.description = summary_from_dict(self.statDict)
    
    def getSummary(self):
        print(self.description)
        
    def getPortfolio(self,
                     returnRates: pd.DataFrame,
                     data: pd.DataFrame | None = None):
        return PortfolioPerformance(self.portfolio,
                                    returnRates,
                                    self.freq,
                                    self.model,
                                    self.risk_method,
                                    data=data)