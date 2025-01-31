from datetime import datetime as dt, timedelta as tmd

def now(date_only: bool = True):
    if date_only: return dt.now().strftime("%Y-%m-%d")
    else: return dt.now().strftime("%Y-%m-%d %H:%M:%S")
    
def round_to_nearest_hour(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour) + tmd(hours=t.minute//30))
    
def str_to_UNIX(date):
    date_dt = dt.strptime(date, '%Y-%m-%d %H:%M:%S')
    date_tmp = dt.timestamp(date_dt)
    return int(date_tmp * 1000)
    
def shift_date(date: str, days: int):
    return dt.strptime(date, "%Y-%m-%d") + tmd(days=days)

def recalculate_frequency(freq):
    if freq[-1].lower() == 'd':
        k = int(freq[:-1])
    elif freq[-1].lower() == 'w':
        k = int(freq[:-1])*5
    elif freq[-1].lower() == 'm':
        k = int(freq[:-1])*22
    elif freq[-1].lower() == 'y':
        k = int(freq[:-1])*252
    return k
    