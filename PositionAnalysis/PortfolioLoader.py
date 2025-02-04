import pandas as pd
from importlib import reload

import PositionAnalysis.PortfolioPerformance
reload(PositionAnalysis.PortfolioPerformance)
from PositionAnalysis.PortfolioPerformance import PortfolioPerformance

import Functions.FileCommunication
reload(Functions.FileCommunication)
from Functions.FileCommunication import *

import Functions.TimeFunctions
reload(Functions.TimeFunctions)
from Functions.TimeFunctions import *

import Functions.StatisticalFunctions
reload(Functions.StatisticalFunctions)
from Functions.StatisticalFunctions import *

import Functions.TechnicalFunctions
reload(Functions.TechnicalFunctions)
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