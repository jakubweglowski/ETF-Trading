import pickle 
import pandas as pd

def SaveDict(dict, filename, filepath: str = 'Data'):
    with open(f'{filepath}/' + f'{filename}.pkl', 'wb') as f:
        pickle.dump(dict, f)
        
def LoadDict(filename, filepath: str = 'Data'):        
    with open(f'{filepath}/' + f'{filename}.pkl', 'rb') as f:
        return pickle.load(f)
    
def SaveData(data: pd.DataFrame | pd.Series, filename, filepath: str = 'Data'):
    data.to_csv(f"{filepath}/"+f"{filename}.csv", sep=",", index=True, header=True)
    
def LoadData(filename, filepath: str = 'Data'):
    return pd.read_csv(f"{filepath}/"+f"{filename}.csv", sep=",", index_col='Date')