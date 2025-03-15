import APICommunication.config as cfg
user_id = cfg.user_id
pwd = cfg.pwd

from datetime import datetime as dt
from Data.DataLoader import *
from Functions.FileCommunication import *

dl = DataLoader(user_id, pwd)

print(f"[INFO] Pobieramy informacje o instrumentach: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
info = dl.getInstrumentsInfo()
# info = dl.loadInstrumentsInfo(filepath='./Data')
SaveDict(info, 'InstrumentsInfo', filepath='./Data')
print("[INFO] Informacje zostały pobrane i skutecznie załadowane.")

print(f"[INFO] Pobieramy historyczne kursy instrumentów: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
# symbols = [key for key, val in info.items()]
# data = dl.getInstrumentsData(symbols, '2016-07-01', '2025-02-17', verbose=True)
data = dl.loadInstrumentsData('2025-02-27', '2025-03-14', filename='InstrumentsData', filepath='./Data', verbose=True)
# SaveData(data, 'InstrumentsData2', filepath='./Data')