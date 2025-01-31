import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt, timedelta as tmd
from IPython.display import display
from importlib import reload

import APICommunication.config as cfg

import Data.DataLoader
reload(Data.DataLoader)
from Data.DataLoader import *

import Data.DataCleaner
reload(Data.DataCleaner)
from Data.DataCleaner import *

import MarkowitzAnalysis.ReturnAnalysis
reload(MarkowitzAnalysis.ReturnAnalysis)
from MarkowitzAnalysis.ReturnAnalysis import *

import PositionAnalysis.PortfolioPerformance
reload(PositionAnalysis.PortfolioPerformance)
from PositionAnalysis.PortfolioPerformance import *

from warnings import filterwarnings
filterwarnings('ignore')

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_experimental_option('excludeSwitches', ['enable-logging'])

def getTER(symbols, file_path='InstrumentsTER', folder_path='Data'):   
    TER = {}
    path = f"{folder_path}/{file_path}.csv"
    with open(path, 'w') as f:
        for i, symbol in enumerate(symbols):
            if i % 50 == 0: print(f"Pozostało {(1-i/len(symbols)):.1%}")
            print(f"Pobieramy TER dla {symbol}")
            url = f'https://www.justetf.com/en/search.html?50-1.0-container-tabsContentContainer-tabsContentRepeater-1-container-content-etfsTablePanel&search=ETFS&query={symbol[:-3]}&_wicket=1'
            # url = f'https://www.justetf.com/en/search.html?query={symbol[:-3]}'
            
            driver = webdriver.Chrome(options=options)
            try:
                driver.get(url)
                time.sleep(1.5)
            except:
                print(f"\t[BŁĄD] Błąd połączenia z internetem. Zasypiamy na 3 minuty.")
                driver.quit() 
                time.sleep(180)
                driver = webdriver.Chrome(options=options)
                try:
                    driver.get(url)
                except:
                    print(f"\t[BŁĄD] Nadal błąd połączenia z internetem. Zapisuję 'None' i kontynuuję.")
                    driver.quit()
                    TER[symbol] = None
                    print(f'{symbol},', file=f)
                    continue
            
            
            try:
                driver.find_element(By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll').click()
                time.sleep(1.5)
            except:
                print("\t[BŁĄD] Błąd przejścia przez warstwę Cookies. Zasypiamy na 3 minuty.")
                driver.quit() 
                time.sleep(180)
                driver = webdriver.Chrome(options=options)
                try:
                    driver.get(url)
                    time.sleep(1.5)
                except:
                    print(f"\t[BŁĄD] Błąd połączenia z internetem. Zasypiamy na 3 minuty.")
                    driver.quit() 
                    time.sleep(180)
                    driver = webdriver.Chrome(options=options)
                    try:
                        driver.get(url)
                    except:
                        print(f"\t[BŁĄD] Nadal błąd połączenia z internetem. Zapisuję 'None' i kontynuuję.")
                        driver.quit()
                        TER[symbol] = None
                        print(f'{symbol},', file=f)
                        continue
                
                try:
                    driver.find_element(By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll').click()
                    time.sleep(1.5)
                except:
                    print("\t[BŁĄD] Ponowny błąd przejścia przez warstwę Cookies")
                    TER[symbol] = None
                    print(f'{symbol},', file=f)
                    driver.quit()
                    continue
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tr = soup.find('tr', class_='odd')
            try:
                td = tr.find_all('td', class_='tal-right')
            except:
                print(f"\t[BŁĄD] Nie znaleziono TER dla {symbol}. Zapisuję 'None' i kontynuuję.")
                TER[symbol] = None
                print(f'{symbol},', file=f)
            
            try:
                ter = float(td[1].text.strip('%'))
                TER[symbol] = ter
                print(f"{symbol},{ter}", file=f)
                print(f"\t[SUKCES]")
            except:
                print(f"\t[BŁĄD] Błąd pobierania TER dla {symbol}. Zapisuję 'None' i kontynuuję.")
                TER[symbol] = None
                print(f'{symbol},', file=f)
                
            driver.quit()
            time.sleep(10)
        
    return TER

if __name__ == "__main__":
    
    start, end = '2023-07-01', '2024-12-23'

    print(f"[INFO] Rozpoczynam pracę programu: {now(False)}")

    dataloader = DataLoader(cfg.user_id, cfg.pwd)
    data = dataloader.loadInstrumentsData(start, end)
    info = dataloader.loadInstrumentsInfo()
    ETFsymbols = [x.strip('_9') for x in info.keys() if x not in ['EURPLN', 'USDPLN', 'GBPPLN', 'CHFPLN']]
    
    TER = getTER(ETFsymbols)
    SaveDict(TER, 'InstrumentsTER', 'Data')