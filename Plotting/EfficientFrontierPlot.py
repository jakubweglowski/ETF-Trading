import pandas as pd
from numpy.random import dirichlet
import matplotlib.pyplot as plt
import matplotlib as mpl

from MarkowitzAnalysis.ReturnAnalysis import *

from PortfolioAnalysis.PortfolioPerformance import *


cmap = mpl.colormaps['Wistia']
colors = cmap(np.linspace(0.2, 1, 7))

class EfficientFrontierPlot:
    def __init__(self, 
                 returnRates: pd.DataFrame, 
                 freq: str,
                 risk_method: str = 'oas',
                 Npoints: int = 80):
        self.returnRates = returnRates
        self.freq = freq
        self.risk_method = risk_method
        
        self.points_to_plot = {}
        self.instruments_to_plot = {}
        
        self.max_sharpe_return = None
        self.max_sharpe_risk = None
        
        self.max_utility = {}
        
        self.fig = None
        
        self._prepare_data_to_plot(Npoints)
    
    def _prepare_data_to_plot(self, Npoints, shift: float = 0.0015):
        
        print("[INFO] Przygotowuję dane do wykresu...")
        
        min_target = self.returnRates.mean().min() + shift
        max_target = self.returnRates.mean().max() - shift
        targets = np.linspace(min_target, max_target, Npoints)

        # rysujemy 'efficient frontier'
        for i, target in enumerate(targets):
            if i % 10 == 0: print(f"\tPozostało {(1-i/len(targets)):.1%}")
            mo = MarkowitzOptimization(self.returnRates, self.freq, verbose=False)
            mo.getOptimalWeights(model='target_return',
                                 risk_method=self.risk_method,
                                 target_return=target)
            portfolio = mo.getPortfolio()
            statDict = portfolio.getStatDict()
            portfolio_results = {key: (val, statDict['OczekiwaneRyzyka'][key])
                                for key, val in statDict['OczekiwaneZwroty'].items()}
            
            self.points_to_plot[statDict['OczekiwanyZwrotPortfela']] = statDict['OczekiwaneRyzykoPortfela']
            for key, val in portfolio_results.items():
                if self.instruments_to_plot.get(key) is None:
                    self.instruments_to_plot[key] = val

        # rysujemy 'max_sharpe'
        print(f"[INFO] Wyznaczamy portfel 'max_sharpe'...")
        mo = MarkowitzOptimization(self.returnRates, self.freq, verbose=False)
        mo.getOptimalWeights(model='max_sharpe', risk_method=self.risk_method)
        portfolio = mo.getPortfolio()
        statDict = portfolio.getStatDict()
        portfolio_results = {key: (val, statDict['OczekiwaneRyzyka'][key])
                                for key, val in statDict['OczekiwaneZwroty'].items()}
        for key, val in portfolio_results.items():
            if self.instruments_to_plot.get(key) is None:
                self.instruments_to_plot[key] = val

        self.max_sharpe_return = statDict['OczekiwanyZwrotPortfela']
        self.max_sharpe_risk = statDict['OczekiwaneRyzykoPortfela']
        
        # rysujemy 'max_utility'
        print(f"[INFO] Wyznaczamy portfele 'max_utility'...")
        mo = MarkowitzOptimization(self.returnRates, self.freq, verbose=False)
        for ra in [15., 30., 60., 100., 150., 200., 300.]:
            mo.getOptimalWeights(model='max_utility', risk_method=self.risk_method, risk_aversion=ra)
            portfolio = mo.getPortfolio()
            statDict = portfolio.getStatDict()
            portfolio_results = {key: (val, statDict['OczekiwaneRyzyka'][key])
                                    for key, val in statDict['OczekiwaneZwroty'].items()}
            for key, val in portfolio_results.items():
                if self.instruments_to_plot.get(key) is None:
                    self.instruments_to_plot[key] = val

            self.max_utility[ra] = (statDict['OczekiwanyZwrotPortfela'], statDict['OczekiwaneRyzykoPortfela'])


    def plot(self, show: bool = True, Nrandom: int = 0):
        
        self.fig, ax = plt.subplots(figsize=(16, 9), layout='constrained')
        ax.plot(self.points_to_plot.values(), self.points_to_plot.keys())
        ax.scatter(self.max_sharpe_risk, self.max_sharpe_return,
                   s=30, c='red',
                   label="Portfel 'max_sharpe'")
        
        x = np.zeros(len(self.max_utility))
        y = np.zeros(len(self.max_utility))
        for i, val in enumerate(self.max_utility.values()):
            x[i] = val[1]
            y[i] = val[0]
        ax.scatter(x, y, 
                   s=20, 
                   c=colors)
        
        x = np.zeros(len(self.instruments_to_plot))
        y = np.zeros(len(self.instruments_to_plot))
        for i, val in enumerate(self.instruments_to_plot.values()):
            x[i] = val[1]
            y[i] = val[0]
        ax.scatter(x, y,
                   s=20,
                   c='black')
            
        if Nrandom > 0:
            print(f"[INFO] Generuję {Nrandom} portfeli losowych...")
            
            # rP = randomPortfolio(self.returnRates.columns)
            # for i in range(Nrandom//2):
            #     if i % 500 == 0: print(f"\tPozostało {(1-i/Nrandom):.1%}")
            #     m, s = rP.getStats(self.returnRates, self.freq, self.risk_method)
            #     # print(f"{s=:.2f}, {m=:.2f}")
            #     ax.scatter(x=s, y=m, s=10, c='limegreen')
                
            x = np.zeros(Nrandom)
            y = np.zeros(Nrandom)
            rP = randomPortfolio(self.instruments_to_plot.keys())
            for i in range(Nrandom):
                if i % 500 == 0: print(f"\tPozostało {(1-i/Nrandom):.1%}")
                m, s = rP.getStats(self.returnRates, self.freq, self.risk_method)
                x[i] = s
                y[i] = m
                # print(f"{s=:.2f}, {m=:.2f}")
            ax.scatter(x, y, s=10, c='darkgreen')
        
        print("[INFO] Rysuję wykres...")
        
        xmin, xmax = ax.get_xlim()
        ax.hlines(0, xmin, xmax, color='red')
        ax.grid(True, which='major')
        ax.grid(True, which='minor', alpha=0.2)
        ax.minorticks_on()
        ax.set_xlabel("Ryzyko portfela [%]")
        ax.set_ylabel("Stopa zwrotu z portfela [%]")
        ax.legend(loc='upper left')

        self.fig.suptitle(f"Efficient Frontier: {self.freq}")
        if show:
            plt.show()
        else:
            plt.close('all')
            
            
            
class randomPortfolio:
      def __init__(self, symbols: list):
            self.symbols = symbols
            
      def generate(self):
            Nsymbols = len(self.symbols)
            weights = dirichlet([1.]*Nsymbols)
            pf = {x: 100*weights[i]
                  for i, x in enumerate(self.symbols)}
            return pf

      def getStats(self, returnRates: pd.DataFrame, freq: str, risk_method: str):
            pf = self.generate()
            portfolio = PortfolioPerformance(portfolio=pf,
                                             returnRates=returnRates,
                                             freq=freq,
                                             risk_method=risk_method)
            return 100*portfolio.portfoliomean, 100*portfolio.portfoliosigma