import pandas as pd
from datetime import datetime as dt, timedelta as tmd
from importlib import reload

import APICommunication.config as cfg
user_id = cfg.user_id
pwd = cfg.pwd

import Data.DataLoader
reload(Data.DataLoader)
from Data.DataLoader import *

import Functions.FileCommunication
reload(Functions.FileCommunication)
from Functions.FileCommunication import *

dl = DataLoader(user_id, pwd)

print(f"[INFO] Pobieramy informacje o instrumentach: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
# info = dl.getInstrumentsInfo()
info = dl.loadInstrumentsInfo(filepath='./Data')
# SaveDict(info, 'InstrumentsInfo', filepath='./Data')
print("[INFO] Informacje zostały pobrane i skutecznie załadowane.")

print(f"[INFO] Pobieramy historyczne kursy instrumentów: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
symbols = [key for key, val in info.items()]
data = dl.getInstrumentsData(symbols, '2015-12-31', '2025-02-03', verbose=True)
# data = dl.loadInstrumentsData('2015-12-31', '2025-02-03', filename='InstrumentsData', filepath='./Data', verbose=True)
SaveData(data, 'InstrumentsData1', filepath='./Data')