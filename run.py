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
info = dl.getInstrumentsInfo()
# symbols = [key for key, val in info.items()]
# data = dl.getInstrumentsData(symbols, '2020-01-01', '2025-01-14', verbose=True)
data = dl.loadInstrumentsData('2020-01-01', '2025-01-13', filename='InstrumentsData', filepath='./Data', verbose=True)

SaveDict(info, 'InstrumentsInfo', filepath='./Data')
# SaveData(data, 'InstrumentsData1', filepath='./Data')