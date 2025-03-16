import pandas as pd
import yfinance as yf
from datetime import datetime as dt

from Functions.TimeFunctions import *
from Functions.Items import *

def reasonProperSymbol(symbol: str) -> str:
    
    # może być tak, że symbol jest poprawny od razu
    try:
        getSymbol(symbol=symbol, period='1D', start='2025-01-01', end='2025-02-01')
        return symbol
    except:
        pass
    
    # usuwamy obecną końcówkę i szukamy poprawnej
    dot_index = symbol.find('.')
    s = symbol[:dot_index] # jeśli symbol = 'P500.DE', to s = 'P500'
    
    endings = ['.L', '.MI', '.PA', '.SW', 
               '.DE', '.MU', '.SG', '.UK', 
               '.WA', '.AS', '.XC', '.XD', 
               '.MC', '']
    for ending in endings:
        try:
            # dokładamy nową końcówkę i sprawdzamy, czy da się pobrać symbol
            getSymbol(symbol=s+ending, period='1D', start='2025-01-01', end='2025-02-01')
            print(f"\t[INFO] Znaleziono poprawny ticker dla {symbol}: {s+ending}.")
            return s+ending
        except:
            # próbujemy z inną końcówką
            time.sleep(3)
            continue
                 
    print(f"\t[BŁĄD] Nie udało się znaleźć poprawnej końcówki dla {symbol}.")
    return ''


def alterSymbol(symbol: str) -> str:
    """Funkcja zmieniająca symbol na taki, który może być użyty w serwisie Yahoo Finance.
    Na przykład 'GBPUSD_59' zmienia na 'GBPUSD=X', 'VOW3.UK' na 'VOW3.L', 'AAPL.US' na 'AAPL'.

    Args:
        symbol (str): _description_

    Returns:
        str: _description_
    """
    
    s = symbol.rstrip('_59')
    if s in currencies: s = s+'=X'
    elif s.find('.UK') != -1: s = s.replace('.UK', '.L')
    elif s.find('.FR') != -1: s = s.replace('.FR', '.PA')
    elif s.find('.NL') != -1: s = s.replace('.NL', '.AS')
    elif s.find('.PL') != -1: s = s.replace('.PL', '.WA')
    elif s.find('.ES') != -1: s = s.replace('.ES', '.MC')
    elif s.find('.US') != -1: s = s.strip('.US')
    else: pass

    return s


def getSymbol(symbol: str, 
              period: str, 
              start: str | None, 
              end: str | None,
              just_now: bool = False) -> pd.Series:
    """Funkcja pobierająca dane dla danego symbolu z serwisu Yahoo Finance.
    W przypadku just_now=True pobierane są dane z ostatniej minuty.

    Args:
        symbol (str): _description_
        period (str): _description_
        start (str | None): _description_
        end (str | None): _description_
        just_now (bool, optional): _description_. Defaults to False.

    Returns:
        pd.Series: _description_
    """
    
    ticker = yf.Ticker(symbol)
    
    if just_now:
        y = ticker.history(period='1D', interval='1m', progress=False)['Close']
        return y[-1]
    
    else:
        y = ticker.history(start=start, end=end, interval=period)['Close']
        assert len(y) > 0, f"Brak danych dla {symbol} w okresie od {start} do {end}."
        y.index = y.index.strftime('%Y-%m-%d')
        y = y.rename(symbol)
        
        time.sleep(2)
        
        return y
    
    
def getCurrencies(info: dict, margin=0.005) -> dict:
    """Wgrywamy kursy walutowe w chwili obecnej.
    Wartości bid i ask są obliczane na podstawie spreadu.

    Args:
        info (dict): _description_
        margin (float, optional): _description_. Defaults to 0.005.

    Returns:
        dict: _description_
    """
    currency_prices = {'bid': {}, 'ask': {}}
    
    for currency_symbol in currencies:
        response = getSymbol(symbol=currency_symbol+'=X', just_now=True)
        try:
            currency_bid = response['bid']
            currency_ask = currency_bid + info[currency_symbol]['SpreadAbs']
        except:
            print(f"[BŁĄD] Błąd pobierania danych: nie można pobrać aktualnego kursu walutowego {currency_symbol}.")
            currency_bid = 0.0
            currency_ask = 0.0

        currency_prices['bid'][currency_symbol] = currency_bid*(1.0-margin)
        currency_prices['ask'][currency_symbol] = currency_ask*(1.0+margin)
    
    return currency_prices


def summary_from_dict(statDict: dict) -> str:
    """Generuje opis statystyk portfela zapisanych w statDict.

    Args:
        statDict (dict): _description_

    Returns:
        str: _description_
    """
    summary = f"Opis wygenerowany {statDict['CzasAnalizy']}.\n"
    try:
        summary += f"Czas otwarcia pozycji: {statDict['CzasOtwarcia']}.\n"
    except KeyError:
        pass
    summary += f"Okres inwestycji: {statDict['OkresInwestycji']}.\n"
    summary += f"Zastosowane kryterium wyboru: {statDict['Model']}.\n"
    summary += f"Metoda estymacji ryzyka: {statDict['MetodaEstymacjiRyzyka']}.\n"
    summary += f"Poziom ufności: {statDict['PoziomUfności']}.\n"
    summary += f"Oczekiwany zwrot z portfela [%]: {statDict['OczekiwanyZwrotPortfela']}\n"
    summary += f"Oczekiwane ryzyko portfela [%]: {statDict['OczekiwaneRyzykoPortfela']}\n"      
    summary += f"Przedział ufności dla stóp zwrotu [%]: "
    for key, val in statDict['PrzedziałUfnościZwrotuPortfela'].items():
        if key == 'lowCI': summary += f"[{val}, "
        elif key == 'highCI': summary += f"{val}]\n"
        
    summary += f"Sharpe Ratio portfela: {statDict['SharpeRatio']}\n"

    tempDict = dict(pd.DataFrame([pd.Series(statDict['SkładPortfela'], name='Waga w portfelu [%]'),
                pd.Series(statDict['OczekiwaneZwroty'], name='Oczekiwana stopa zwrotu [%]'),
                pd.Series(statDict['OczekiwaneRyzyka'], name='Oczekiwana stopa ryzyka [%]'),
                pd.DataFrame(statDict['PrzedziałyUfnościZwrotów']).T.iloc[:, 0],
                pd.DataFrame(statDict['PrzedziałyUfnościZwrotów']).T.iloc[:, 1]]))
        
    summary += "Skład portfela:\n"
    for key, val in tempDict.items():
        summary += f"\t{key}:\n"
        for key1, val1 in dict(val).items():
            if key1 == 'lowCI': summary += f"\t\tPrzedział ufności dla stóp zwrotu [%]: [{val1}, "
            elif key1 == 'highCI': summary += f"{val1}]\n"
            else: summary += f"\t\t{key1}: {val1}\n"
    return summary

def decode_compare(compare: str):
    """Funkcja dekodująca argument 'compare' postaci 'metoda_okno'.
    Na przykład 'sma_20' oznacza średnią ruchomą prostą z oknem 20.
    Wtedy funkcja zwraca krotkę ('sma', 20).

    Args:
        compare (str): _description_

    Returns:
        _type_: _description_
    """
    compare = compare.lower()
    assert compare.find('_') != -1, "Argument 'compare' musi mieć format 'metoda_okno'."

    method = compare[:3]
    assert method in ['sma', 'ema'], "Metodą musi być 'sma' albo 'ema'."

    window = compare[compare.find('_')+1:]
    window = recalculate_frequency(window)
    
    return method, window
                