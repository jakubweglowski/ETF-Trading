import pandas as pd
from Functions.FileCommunication import *
from Functions.TimeFunctions import *
from Functions.StatisticalFunctions import *
from Functions.TechnicalFunctions import *

class PortfolioPerformance:
    def __init__(self,
                 portfolio: dict,
                 returnRates: pd.DataFrame,
                 freq: str,
                 risk_method: str,
                 model: str | None = None, 
                 risk_free_rate: float = 0.0575,
                 data: pd.DataFrame | None = None):
        
        assert isinstance(freq, str), "Argument 'freq' musi być klasy 'str'."
        self.freq = freq
        self.k = recalculate_frequency(self.freq)     
        self.risk_free_rate = risk_free_rate*self.k/252
        
        self.portfolio = portfolio
        self.symbols = list(self.portfolio.keys())
        self.weights = np.array(list(self.portfolio.values()))/100
        
        self.returnRates = returnRates.loc[:, self.symbols]
        
        if data is not None: 
            self.portfolioPrice = (self.weights * data.loc[:, self.symbols]).sum(axis=1)
            
        self.portfolioReturn = (self.weights * self.returnRates).sum(axis=1)
        
        self.portfoliomean = self.portfolioReturn.mean()
        self.Cov = pd.DataFrame(self.getCov(risk_method), index = self.symbols, columns=self.symbols)
        self.portfoliosigma = np.sqrt(self.weights @ np.array(self.Cov) @ self.weights)
        self.instrumentsigmas = pd.Series(np.sqrt(np.diag(np.array(self.Cov))), index=self.symbols)
        self.sharpe_ratio = (self.portfoliomean - self.risk_free_rate)/self.portfoliosigma
        
        # Do zapisania w podsumowaniu
        self.model = model
        self.risk_method = risk_method
    
    def getCov(self, method: str):
        Cov = getRisk(self.returnRates, method)
        return Cov
    
    def getStatDict(self, alphaCI: float = 0.05):
        statDict = {'OczekiwanyZwrotPortfela': round(100*self.portfoliomean, 4),
                         'OczekiwaneRyzykoPortfela': round(100*self.portfoliosigma, 4),
                         f'PrzedziałUfnościZwrotuPortfela': {
                            f'lowCI': round(100*getQuantiles(self.portfolioReturn, alphaCI)[0], 4),
                            f'highCI': round(100*getQuantiles(self.portfolioReturn, alphaCI)[1], 4)},
                         'SharpeRatio': round(self.sharpe_ratio, 4),
                         'SkładPortfela': self.portfolio}
        
        statDict['OczekiwaneZwroty'] = dict(round(100*getExpectedReturns(self.returnRates), 4))
        statDict['OczekiwaneRyzyka'] = dict(round(100*self.instrumentsigmas, 4))
        statDict[f'PrzedziałyUfnościZwrotów'] = dict(pd.DataFrame({
            f'lowCI': dict(round(100*self.returnRates.apply(lambda x: getQuantiles(x, alphaCI)[0]), 4)),
            f'highCI': dict(round(100*self.returnRates.apply(lambda x: getQuantiles(x, alphaCI)[1]), 4))
        }).T)
        for key, val in statDict[f'PrzedziałyUfnościZwrotów'].items():
            statDict[f'PrzedziałyUfnościZwrotów'][key] = dict(val)
        statDict['OkresInwestycji'] = self.freq
        statDict['Model'] = self.model
        statDict['MetodaEstymacjiRyzyka'] = self.risk_method
        statDict['PoziomUfności'] = 1-alphaCI
        statDict['CzasAnalizy'] = now(False)
        
        return statDict
        
    def getSummary(self,
                   verbose: bool = True,
                   save_dict: bool = False,
                   save_text: bool = False,
                   filename: str | None = None,
                   filepath: str | None = None):
        
        statDict = self.getStatDict()
        summary = summary_from_dict(statDict)
        if verbose: print(summary)
        if save_dict or save_text:
            assert filename is not None and filepath is not None, "[BŁĄD] Jeśli chcesz zapisać wynik analizy, musisz podać ścieżkę do pliku (argumenty 'filename' i 'filepath')."
            if save_dict:
                statDict['Rodzaj'] = 'Rekomendacja'
                SaveDict(statDict, filename, filepath)
            if save_text:
                with open(f"{filepath}/{filename}.txt", 'w', encoding='utf-8') as f:
                    f.write(summary)