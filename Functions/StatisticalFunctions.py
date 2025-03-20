# Obliczamy zwrot w okresie 'freq'
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from sklearn.covariance import OAS, EmpiricalCovariance, LedoitWolf, ShrunkCovariance
from qpsolvers import solve_qp

def getMeanCovariance(df: pd.DataFrame) -> tuple:
    mu = df.mean() # expected returns
    S = df.cov() # covariance matrix
    
    tickers_to_drop = list(mu[mu.isna()].index)
    mu = mu.dropna()
    S = S.drop(columns = tickers_to_drop, index = tickers_to_drop)
    
    return (mu, S)

def getExpectedReturns(data):
    mu = data.mean() # expected returns
    return mu.dropna()

def getCValue(y: pd.Series):
    n = len(y)
    c = np.array(range(1, n+1))
    corr, p = pearsonr(c, np.array(y.values))
    if p > 0.05: corr = 0.0 # korelacja jest pozorna
    return corr

def getRSI(y: pd.Series):
    U = y[y>0].sum()
    D = y[y<0].sum()
    RS = -U/D
    RSI = 100-100/(1+RS)
    return RSI

def getReturnRates(bidPrice, askPrice, k):
    assert isinstance(k, int), "[BŁĄD] Argument 'k' musi być typu 'int'."
    return (bidPrice/askPrice.shift(k) - 1).dropna()
    
def getRisk(data: pd.DataFrame, method: str):
    method = method.lower()
    assert method in ['oas', 'ledoit-wolf', 'shrinkage', 'empirical'], "[BŁĄD] Nie podano metody estymacji ryzyka lub też podana metoda nie jest zaimplementowana."
    if method.lower() == 'oas':
        risk_model = OAS()
        Cov = risk_model.fit(data).covariance_
    elif method.lower() == 'empirical':
        risk_model = EmpiricalCovariance()
        Cov = risk_model.fit(data).covariance_
    elif method.lower() == 'ledoit-wolf':
        risk_model = LedoitWolf()
        Cov = risk_model.fit(data).covariance_
    elif method.lower() == 'shrinkage':
        risk_model = ShrunkCovariance()
        Cov = risk_model.fit(data).covariance_
    return Cov

def getQuantiles(y: pd.Series, q: float = 0.05, one_sided: bool = False, type_: str = 'minmax'):
        assert q >= 0 and q <= 0.5, "[BŁĄD] Kwantyl musi być liczbą od 0 do 0.5."
        assert type_.lower() in ['minmax', 'values'], "[BŁĄD] Argument 'type_' musi być jednym z 'minmax', 'values'."
        
        if not one_sided: ymiddle = y.iloc[(y >= y.quantile(q)).values & (y <= y.quantile(1-q)).values]
        else: ymiddle = y.iloc[(y <= y.quantile(1-q)).values]
        
        if type_.lower() == 'minmax': return (ymiddle.min(), ymiddle.max())
        else: return ymiddle

def SMA(y: pd.Series):
    return y.mean()

def EMA(y: pd.Series, alpha: float):
    weights = np.array([(1-alpha)**(len(y)-i+1) for i in range(len(y))])
    return (y.values).dot(weights)/np.sum(weights)

def Smoothen(data: pd.DataFrame, window: int, method: str, alpha: float = 0.1):
    method = method.lower()
    assert method in ['sma', 'ema'], "[BŁĄD] Podana metoda nie jest zaimplementowana."
    if method == 'sma':
        return data.dropna().rolling(window).mean()
    else:
        return data.dropna().rolling(window).apply(lambda y: EMA(y, alpha))

possible_volatility_measures = ['pct', 'abs', 'exp']
def Volatility(y1, y2, measure: str ='pct'):
    measure = measure.lower()
    assert measure in possible_volatility_measures, "[BŁĄD] Podana miara zmienności nie jest zaimplementowana."
    if measure == 'pct':
        return 100*(y1/y2 - 1)
    elif measure == 'abs':
        return 100*np.abs(y1/y2 - 1)
    elif measure == 'exp':
        return 100*(np.exp(y1/y2 - 1) - 1)

def solveLP(expected_returns: pd.Series,
            covariance_matrix: pd.DataFrame,
            mean_weight: float = 1.,
            sigma_weight: float = 1.,
            verbose: bool = False) -> tuple:
    
    # transform data into matrices
    expected_returns = np.array(expected_returns)
    covariance_matrix = np.array(covariance_matrix)
    
    if verbose: print("Rozwiązujemy zadanie optymalizacyjne...")
    weights = solve_qp(P = sigma_weight * covariance_matrix,
                       q = -mean_weight * expected_returns,
                       A = np.array([1.]*expected_returns.shape[0]),
                       b = np.array([1.]),
                       G = -np.eye(expected_returns.shape[0]),
                       h = np.zeros_like(expected_returns),
                       solver='cvxopt')
    if verbose: print("koniec!")
    
    sigma = np.sqrt(weights @ np.array(covariance_matrix) @ weights)
    mean = expected_returns.dot(weights)
        
    return weights, mean, sigma
