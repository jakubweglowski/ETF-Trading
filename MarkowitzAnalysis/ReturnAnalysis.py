import pandas as pd
from Functions.FileCommunication import *
from Functions.TimeFunctions import *
from Functions.StatisticalFunctions import *
from Functions.TechnicalFunctions import *
from PortfolioAnalysis.PortfolioPerformance import PortfolioPerformance

from pypfopt.efficient_frontier import EfficientFrontier

class MarkowitzOptimization:
    
    def __init__(self,
                 returnRates: pd.DataFrame,
                 freq: str,
                 verbose: bool = True):
        
        self.freq = freq
        self.k = recalculate_frequency(freq)
        
        self.returnRates = returnRates
        self.symbols = list(self.returnRates.columns)
        
        self.portfolio = None
        self.analysis_performed = False
        
        if verbose: print(f"[INFO] Załadowano {len(self.symbols)} instrumentów.")
    
    def _analysis_performed(self):
        self.analysis_performed = True
        
    def getOptimalWeights(self, 
                          model: str = 'max_utility', 
                          risk_method: str = 'oas',
                          risk_free_rate: float = 0.0575, # dla Sharpe Ratio
                          target_return: float = 0.1, # dla metody 'target_return'
                          risk_aversion: float = 20.0 # dla metody 'max_utility'
                          ):
        
        model = model.lower()
        assert model in ['max_utility',
                         'max_sharpe',
                         'target_return',
                         'min_volatility'], "[BŁĄD] Podano metodę, która nie jest zaimplementowana."
        
        risk_free_rate = risk_free_rate*self.k/252
        mu, Cov = getExpectedReturns(self.returnRates), getRisk(self.returnRates, risk_method)
        
        if model == 'max_utility':
            weights, opt_return, opt_risk = solveLP(mu, Cov, sigma_weight=risk_aversion)
            opt_sharpe = (opt_return - risk_free_rate)/opt_risk
            portfolio = {x: round(100*weights[i], 4) for i, x in enumerate(self.symbols) if 100*weights[i] >= 1.0}

        elif model == 'max_sharpe':
            ef = EfficientFrontier(mu, Cov, solver='CVXOPT')
            ef.max_sharpe(risk_free_rate)
            opt_return, opt_risk, opt_sharpe = ef.portfolio_performance(risk_free_rate=risk_free_rate)
            weights = ef.weights
            portfolio = {key: round(val*100, 4) for key, val in ef.clean_weights().items() if 100*val > 1.0}
        
        elif model == 'target_return':
            ef = EfficientFrontier(mu, Cov, solver='CVXOPT')
            ef.efficient_return(target_return)
            opt_return, opt_risk, opt_sharpe = ef.portfolio_performance()
            weights = ef.weights
            portfolio = {key: round(val*100, 4) for key, val in ef.clean_weights().items() if 100*val > 1.0}
        
        elif model == 'min_volatility':
            ef = EfficientFrontier(mu, Cov, solver='CVXOPT')
            ef.min_volatility()
            opt_return, opt_risk, opt_sharpe = ef.portfolio_performance()
            weights = ef.weights
            portfolio = {key: round(val*100, 4) for key, val in ef.clean_weights().items() if 100*val > 1.0}
            
        assert np.isclose(np.sum(weights), 1.0), f"[BŁĄD] Suma wag w portfelu powinna wynosić 100%."
        
        self.portfolio = PortfolioPerformance(portfolio=portfolio, 
                                              returnRates=self.returnRates, 
                                              freq=self.freq, 
                                              risk_method=risk_method,
                                              model=model)
        self._analysis_performed()
            
    def getPortfolio(self):
        if self.analysis_performed:
            return self.portfolio
        else:
            print(f"[BŁĄD] Należy najpierw uruchomić metodę 'getOptimalWeights'.")