import pandas as pd
import matplotlib.pyplot as plt

from PortfolioAnalysis.PortfolioPerformance import PortfolioPerformance
from Functions.FileCommunication import *
from Functions.TimeFunctions import *
from Functions.StatisticalFunctions import *
from Functions.TechnicalFunctions import *

class Plotter:
    
    def __init__(self, 
                 symbols: list | dict,
                 data: pd.DataFrame, 
                 returnRates: pd.DataFrame,
                 freq: str,
                 model: str,
                 risk_method: str,
                 volatility_measure: str = 'pct',
                 compare: str | list[str] = 'ema_2w',
                 alpha: float = 0.1):
        
        assert isinstance(symbols, list) or isinstance(symbols, dict), "[BŁĄD] Argument 'symbols' musi być listą symboli albo słownikiem symboli oraz ich wag w portfelu."
        if isinstance(symbols, dict):
            self.pp = PortfolioPerformance(portfolio=symbols,
                                           returnRates=returnRates,
                                           freq=freq,
                                           risk_method=risk_method,
                                           model=model,
                                           data=data)
            self.symbols = self.pp.symbols
        else:
            self.pp = None
            self.symbols = symbols
            
        self.data = data
        self.returnRates = returnRates
        
        assert isinstance(freq, str), "[BŁĄD] Argument 'freq' musi być typu 'str'."
        self.freq = freq
        
        self.volatility_measure = volatility_measure
        self.compare = compare
        self.alpha = alpha
        
        print(f"[INFO] Wygładzamy dane, obliczamy zmienność...")
        if isinstance(self.compare, str):
            method, window = decode_compare(self.compare)
            self.data_smoothed = Smoothen(self.data, window, method, self.alpha)
            self.data_volatility = Volatility(self.data, self.data_smoothed, self.volatility_measure)
        else:
            method1, window1 = decode_compare(self.compare[0])
            self.data_smoothed1 = Smoothen(self.data, window1, method1, self.alpha)
            
            method2, window2 = decode_compare(self.compare[1])
            self.data_smoothed2 = Smoothen(self.data, window2, method2, self.alpha)
            self.data_volatility = Volatility(self.data_smoothed1, self.data_smoothed2, self.volatility_measure)
        
        if isinstance(symbols, dict):
            self.portfoliofig = plt.figure(figsize=(16, 9), layout='constrained')
        self.mainfig = plt.figure(figsize=(16, 9*len(self.symbols)), layout='constrained')
        self.subfigs = self.mainfig.subfigures(len(self.symbols), 1)
    
    def plot_all(self):
        for i, symbol in enumerate(self.symbols):
            self.plot_single(symbol, i)
        if self.pp is not None:
            self.plot_portfolio()
    
    def plot_portfolio(self, alpha: float = 0.1):
        fig = self.portfoliofig
        fig.suptitle(f"Wyniki łączne portfela")
        spec = fig.add_gridspec(2, 2, height_ratios=[1.5, 1])
        
        y = self.pp.portfolioPrice
        ax1 = fig.add_subplot(spec[0, :])
        ax1.plot(y, label=f"Kurs portfela")
        if isinstance(self.compare, str):
            method, window = decode_compare(self.compare)
            y = Smoothen(self.pp.portfolioPrice, window, method, alpha)
            y_volatility = Volatility(self.pp.portfolioPrice, y, self.volatility_measure)
            ax1.plot(y, label=f"Kurs wygładzony {self.compare}")
        else:
            method1, window1 = decode_compare(self.compare[0])
            y1 = Smoothen(self.pp.portfolioPrice, window1, method1, alpha)
            ax1.plot(y1, label=f"Kurs wygładzony {self.compare[0]}")
            
            method2, window2 = decode_compare(self.compare[1])
            y2 = Smoothen(self.pp.portfolioPrice, window2, method2, alpha)
            ax1.plot(y2, label=f"Kurs wygładzony {self.compare[1]}")
            
            y_volatility = Volatility(y1, y2, self.volatility_measure)
            
        ax1.legend()
        ax1.grid(True)

        y = 100*self.pp.portfolioReturn
        lowCI, highCI = getQuantiles(y)
        xmin, xmax = y.index[0], y.index[-1]
        mean = y.mean()
        ax2 = fig.add_subplot(spec[1, 0])
        ax2.plot(y, label=f"Stopa zwrotu {self.freq}")
        ax2.hlines(y=0, color="red", xmin=xmin, xmax=xmax)
        ax2.hlines(y=lowCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax2.hlines(y=highCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax2.hlines(y=mean, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax2.legend()
        ax2.grid(True)

        y = y_volatility
        lowCI, highCI = getQuantiles(y)
        xmin, xmax = y.index[0], y.index[-1]
        mean = y.mean()
        ax3 = fig.add_subplot(spec[1, 1])
        ax3.plot(y, label=f"Zmienność")
        ax3.hlines(y=lowCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax3.hlines(y=highCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax3.hlines(y=mean, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax3.legend()
        ax3.grid(True)
    
    def plot_single(self, symbol: str, position_in_mainfig: int):
        fig = self.subfigs[position_in_mainfig]
        fig.suptitle(f"Instrument: {symbol.strip('_9')}")
        spec = fig.add_gridspec(2, 2, height_ratios=[1.5, 1])
        
        y = self.data.loc[:, symbol]
        ax1 = fig.add_subplot(spec[0, :])
        ax1.plot(y, label=f"Kurs {symbol}")
        if isinstance(self.compare, str):
            y = self.data_smoothed.loc[:, symbol]
            ax1.plot(y, label=f"Kurs wygładzony {self.compare}")
        else:
            y = self.data_smoothed1.loc[:, symbol]
            ax1.plot(y, label=f"Kurs wygładzony {self.compare[0]}")
            
            y = self.data_smoothed2.loc[:, symbol]
            ax1.plot(y, label=f"Kurs wygładzony {self.compare[1]}")
        ax1.legend()
        ax1.grid(True)

        y = 100*self.returnRates.loc[:, symbol]
        lowCI, highCI = getQuantiles(y)
        xmin, xmax = y.index[0], y.index[-1]
        mean = y.mean()
        ax2 = fig.add_subplot(spec[1, 0])
        ax2.plot(y, label=f"Stopa zwrotu {self.freq} [%]")
        ax2.hlines(y=0, color="red", xmin=xmin, xmax=xmax)
        ax2.hlines(y=lowCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax2.hlines(y=highCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax2.hlines(y=mean, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax2.legend()
        ax2.grid(True)

        y = self.data_volatility.loc[:, symbol]
        lowCI, highCI = getQuantiles(y)
        xmin, xmax = y.index[0], y.index[-1]
        mean = y.mean()
        ax3 = fig.add_subplot(spec[1, 1])
        ax3.plot(y, label=f"Zmienność")
        ax3.hlines(y=lowCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax3.hlines(y=highCI, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax3.hlines(y=mean, color="red", xmin=xmin, xmax=xmax, linestyles='dashed')
        ax3.legend()
        ax3.grid(True)
        
    def plot(self,
             show_instruments: bool = False,
             show_portfolio: bool = True):
        print(f"[INFO] Rysujemy wykresy...")
        self.plot_all()
        if show_instruments and show_portfolio: plt.plot()
        elif show_instruments and not show_portfolio:
            plt.close(self.portfoliofig)
            plt.plot()
        elif show_portfolio and not show_instruments:
            plt.close(self.mainfig)
            plt.plot()
        else:
            plt.close('all')
            
    