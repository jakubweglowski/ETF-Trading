import pandas as pd
import yfinance as yf
from datetime import datetime as dt

from Functions.TimeFunctions import *
from Functions.StatisticalFunctions import *
from Functions.Items import *

def reasonProperSymbol(symbol: str) -> str:
    """Funkcja sprawdzająca, czy symbol jest poprawny.
    Jeśli nie, to próbuje znaleźć poprawny symbol.

    Args:
        symbol (str): symbol wejściowy

    Returns:
        str: poprawny symbol albo pusty string (jeśli nie udało się znaleźć poprawnego symbolu)
    """
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


class getSymbol:
    """Klasa pobierająca dane z serwisu Yahoo Finance.
    Możliwe jest pobranie danych z określonego okresu (start, end) albo danych z chwili obecnej.

    Args:
        symbol (str): _description_
        period (str | None, optional): _description_. Defaults to None.
        start (str | None, optional): _description_. Defaults to None.
        end (str | None, optional): _description_. Defaults to None.
        just_now (bool, optional): _description_. Defaults to False.

    Returns:
        pd.Series: _description_
    """
    
    def __init__(self):
        pass
    
    def __call__(self,
                 symbol: str, 
                 period: str | None = None, 
                 start: str | None = None, 
                 end: str | None = None,
                 just_now: bool = False) -> pd.Series:
        
        ticker = yf.Ticker(symbol)
        
        if just_now:
            y = ticker.history(period='1d', interval='5m')['Close']
            if len(y) > 0:
                return y[-1]
            else:
                return np.NaN
            
        else:
            y = ticker.history(start=start, end=shift_date(end, 1), interval=period)['Close']
            assert len(y) > 0, f"Brak danych dla {symbol} w okresie od {start} do {end}."
            y.index = unify_time_index(y.index)
            y = y.rename(symbol)
            
            time.sleep(0.25)
            
            return round(y, 4)
    
    
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
        try:
            currency_bid = getSymbol()(symbol=currency_symbol+'=X', just_now=True)
            currency_ask = currency_bid + info[currency_symbol]['SpreadAbs']
        except:
            print(f"[BŁĄD] Błąd pobierania danych: nie można pobrać aktualnego kursu walutowego {currency_symbol}.")
            currency_bid = 0.0
            currency_ask = 0.0

        currency_prices['bid'][currency_symbol] = currency_bid*(1.0-margin)
        currency_prices['ask'][currency_symbol] = currency_ask*(1.0+margin)
    
    return currency_prices

def unify_time_index(old_index):
    """Funkcja ujednolicająca indeks czasowy z mieszanki typów 'Timestamp' oraz 'str'
    na typ 'str'.

    Args:
        old_index (_type_): _description_

    Returns:
        _type_: _description_
    """
    new_index = []
    for i, x in enumerate(old_index):
        if not isinstance(x, str): # jeśli nie jest typu 'str', jest typu 'Timestamp'
            new_index.append(x.strftime('%Y-%m-%d'))
        else:
            new_index.append(x)
    return new_index

def summary_from_dict(statDict: dict) -> str:
    """Generuje opis statystyk portfela zapisanych w statDict.

    Args:
        statDict (dict): _description_

    Returns:
        str: _description_
    """
    summary = f"Czas przeprowadzenia analizy: {statDict['CzasAnalizy']}.\n"
    
    try:
        summary += f"Opisywany obiekt: {statDict['Rodzaj']}.\n"
    except KeyError:
        pass
    
    try:
        summary += f"Czas otwarcia pozycji: {statDict['CzasOtwarcia']}.\n"
    except KeyError:
        pass
    
    summary += f"\nZastosowane kryterium wyboru: {statDict['Model']}.\n"
    summary += f"Metoda estymacji ryzyka: {statDict['MetodaEstymacjiRyzyka']}.\n"
    summary += f"Poziom ufności: {statDict['PoziomUfności']}.\n"
    
    summary += f"\nOkres inwestycji: {statDict['OkresInwestycji']}.\n"
    summary += f"Oczekiwany zwrot z portfela [%]: {statDict['OczekiwanyZwrotPortfela']}\n"
    summary += f"Oczekiwane ryzyko portfela [%]: {statDict['OczekiwaneRyzykoPortfela']}\n"      
    summary += f"\tPrzedział ufności dla stóp zwrotu [%]: "
    for key, val in statDict['PrzedziałUfnościZwrotuPortfela'].items():
        if key == 'lowCI': summary += f"[{val}, "
        elif key == 'highCI': summary += f"{val}]\n"
        else: pass
    summary += f"Sharpe Ratio portfela: {statDict['SharpeRatio']}\n"

        
    tempDict = dict(pd.DataFrame([pd.Series(statDict['SkładPortfela'], name='Waga w portfelu [%]'),
                pd.Series(statDict['OczekiwaneZwroty'], name='Oczekiwana stopa zwrotu [%]'),
                pd.Series(statDict['OczekiwaneRyzyka'], name='Oczekiwana stopa ryzyka [%]'),
                pd.DataFrame(statDict['PrzedziałyUfnościZwrotów']).T.iloc[:, 0],
                pd.DataFrame(statDict['PrzedziałyUfnościZwrotów']).T.iloc[:, 1]]))
        
    summary += "\nSkład portfela:\n"
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


def generateMainSummary(K, 
                        portfolio,
                        symbols,
                        symbol_currencies,
                        opening_symbol_prices,
                        opening_currency_prices,
                        current_currency_prices):
    MainSummary = pd.DataFrame()
        
    current_prices = {}
    for symbol in symbols:
        current_prices[symbol] = getSymbol()(symbol, just_now=True)
        
    MainSummary['Waluta bazowa'] = {symbol: symbol_currencies[symbol] for symbol in symbols}
    MainSummary['Waga w portfelu [%]'] = portfolio
    MainSummary['Wartość początkowa [PLN]'] = K * MainSummary['Waga w portfelu [%]']/100
    
    MainSummary['Kurs początkowy'] = opening_symbol_prices
    MainSummary['Kurs obecny'] = current_prices
    MainSummary['Stopa zwrotu [%]'] = (MainSummary['Kurs obecny']/MainSummary['Kurs początkowy'] - 1)*100
    
    # open_currencies = opening_currency_prices['ask']
    # current_currencies = getCurrencies(info)['bid']
    
    MainSummary['Kurs początkowy [PLN]'] = MainSummary['Kurs początkowy'] * MainSummary['Waluta bazowa'].apply(lambda x: opening_currency_prices[x+'PLN'])
    MainSummary['Kurs obecny [PLN]'] = MainSummary['Kurs obecny'] * MainSummary['Waluta bazowa'].apply(lambda x: current_currency_prices[x+'PLN'])
    MainSummary['Stopa zwrotu [PLN, %]'] = (MainSummary['Kurs obecny [PLN]']/MainSummary['Kurs początkowy [PLN]'] - 1)*100

    MainSummary = MainSummary.round(4)
    return MainSummary

def generateTimeStats(investment_period: str, opening_time: str) -> pd.DataFrame:
    k = recalculate_frequency(investment_period, full=True)
    
    opening_time_dt = dt.strptime(opening_time, "%Y-%m-%d %H:%M:%S")
    now_dt = dt.strptime(now(False), "%Y-%m-%d %H:%M:%S")
    time_passed = now_dt - opening_time_dt
    time_passed_str = f'{time_passed.days} dni {time_passed.seconds//3600} godzin'
    
    closing_date = shift_date(opening_time_dt.strftime("%Y-%m-%d"), k)
    TimeStats = pd.DataFrame({'Okres zawarcia pozycji': {'': f'{k} dni'},
                            'Czas otwarcia pozycji': {'': opening_time},
                            'Obecny czas': {'': now(False)},
                            'Czas od otwarcia': {'': time_passed_str},
                            'Przewidywana data zamknięcia pozycji': {'': closing_date}
                            })
    return TimeStats

def generateCurrenciesSummary(opening_prices, info):
    current_prices = getCurrencies(info)['bid']    
    CurrenciesSummary = pd.DataFrame({'Początkowy kurs walutowy (Ask)': opening_prices['ask'],
                                      'Obecny kurs walutowy (Bid)': current_prices})
    CurrenciesSummary['Stopa zwrotu [%]'] = (CurrenciesSummary['Obecny kurs walutowy (Bid)']/CurrenciesSummary['Początkowy kurs walutowy (Ask)'] - 1)*100
    CurrenciesSummary = CurrenciesSummary.round(4)
    return CurrenciesSummary

def generateReturnStats(K, portfolioExpectedReturn, portfolioReturnCI, levelCI, returns, returnsPLN, weights):
    ReturnStats = pd.DataFrame({'Zwrot z portfela [%]': {'': (returns * weights/100).sum()},
                                'Zwrot z portfela [PLN, %]': {'': (returnsPLN * weights/100.).sum()},
                                'Oczekiwany zwrot z portfela [PLN, %]': {'': portfolioExpectedReturn},
                                f'Przedział ufności ({levelCI}) zwrotu portfela [PLN, %]': f'[{portfolioReturnCI["lowCI"]}, {portfolioReturnCI["highCI"]}]'
                                })
    ReturnStats['Zwrot nominalny [PLN]'] = K * ReturnStats[['Zwrot z portfela [PLN, %]']]/100.
    ReturnStats = ReturnStats.round(4)
    return ReturnStats
                