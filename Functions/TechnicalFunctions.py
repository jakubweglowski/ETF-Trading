import pandas as pd
import yfinance as yf
from datetime import datetime as dt

from Functions.TimeFunctions import *
from Functions.Items import *

def getSymbol(symbol: str, 
              period: str, 
              start: str | None, 
              end: str | None,
              just_now: bool = True) -> pd.Series:
    
    ticker = yf.Ticker(symbol)
    
    if just_now:
        y = ticker.history(period='1D', interval='1m')['Close']
        return y[-1]
    
    else:
        y = ticker.history(start=start, end=end, interval=period)['Close']
        assert len(y) > 0, f"Brak danych dla {symbol} w okresie od {start} do {end}."
        y.index = y.index.strftime('%Y-%m-%d')
        y = y.rename(symbol)
        return y
    
    
def getCurrencies(info: dict, margin=0.005):
        
        # wgrywamy kursy walutowe w chwili obecnej
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


def summary_from_dict(statDict):
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
    compare = compare.lower()
    assert compare.find('_') != -1, "Argument 'compare' musi mieć format 'metoda_okno'."

    method = compare[:3]
    assert method in ['sma', 'ema'], "Metodą musi być 'sma' albo 'ema'."

    window = compare[compare.find('_')+1:]
    window = recalculate_frequency(window)
    
    return method, window
                