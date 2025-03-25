import pandas as pd
from datetime import datetime as dt
from PortfolioAnalysis.PortfolioPerformance import *
from Data.DataLoader import *
from Data.DataCleaner import *
from Functions.FileCommunication import *
from Functions.TimeFunctions import *
from Functions.StatisticalFunctions import *
from Functions.TechnicalFunctions import *

def PortfolioLoader(filename: str,
                    filepath: str):
        
        statDict = LoadDict(filename, filepath)
        
        portfolio = statDict['SkładPortfela']
        freq = statDict['OkresInwestycji']
        k = recalculate_frequency(freq)
        
        model = statDict['Model']
        risk_method = statDict['MetodaEstymacjiRyzyka']
        
        start = shift_date(
            dt.strptime(
                statDict['CzasAnalizy'], 
                "%Y-%m-%d %H:%M:%S"
                ).strftime("%Y-%m-%d"),
            -3*k)
        
        dl = DataLoader()
        data = dl.loadInstrumentsData(start_date=start, end_date=now())
        info = dl.loadInstrumentsInfo()
        
        dc = DataCleaner(data, info, load_only=portfolio.keys())
        returnRates = dc.getReturnRates(freq)

        return PortfolioPerformance(portfolio=portfolio,
                                    returnRates=returnRates,
                                    freq=freq,
                                    risk_method=risk_method,
                                    model=model,
                                    data=data)