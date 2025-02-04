import pandas as pd
from datetime import datetime as dt
from importlib import reload

import Functions.TimeFunctions
reload(Functions.TimeFunctions)
from Functions.TimeFunctions import *

def XTB_to_pandas(response):
    data = pd.DataFrame.from_dict(response['returnData']['rateInfos'])
    digits = response['returnData']['digits']

    data['Date'] = data['ctm'].apply(lambda x: dt.fromtimestamp(x/1000))
    data['Price'] = (data['open'] + data['close'])/(10**digits)
    data = data.loc[:, ['Date', 'Price']]
    data = data.set_index('Date')
    data = data.iloc[:, 0]

    return data

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
                