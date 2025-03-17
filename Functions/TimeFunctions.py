from datetime import datetime as dt, timedelta as tmd
import time

def estimate_time_to_end(iter, n_iters, beginning_time) -> None:
    
    time_of_calc = time.time() - beginning_time
    time_of_calc_min = int(time_of_calc/60) # czas od początku w minutach
    time_of_calc_sec = time_of_calc - 60*time_of_calc_min # czas od początku w sekundach ponad pełną minutę
    
    # estymujemy pozostały czas obliczeń zakładając stałą prędkość obliczeń
    speed_of_calc = time_of_calc/iter
    time_left = speed_of_calc*(n_iters-iter) # pozostały czas w sekundach
    time_left_min = int(time_left/60) # ile minut do końca
    time_left_sec = time_left - 60*time_left_min # ile sekund ponad pełną minutę
    print(f"\t\tCzas od początku pobierania: {time_of_calc_min:.0f} minut {time_of_calc_sec:.0f} sekund.")
    print(f"\t\tEstymowany pozostały czas: {time_left_min:.0f} minut {time_left_sec:.0f} sekund.")
        
def now(date_only: bool = True) -> str:
    if date_only: return dt.now().strftime("%Y-%m-%d")
    else: return dt.now().strftime("%Y-%m-%d %H:%M:%S")
    
def round_to_nearest_hour(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour) + tmd(hours=t.minute//30))
    
def str_to_UNIX(date, full: bool = True) -> int:
    if full: date_dt = dt.strptime(date, '%Y-%m-%d %H:%M:%S')
    else: date_dt = dt.strptime(date, '%Y-%m-%d')
    
    date_tmp = dt.timestamp(date_dt)
    return int(date_tmp * 1000)
    
def shift_date(date: str, days: int) -> str:
    return (dt.strptime(date, "%Y-%m-%d") + tmd(days=days)).strftime("%Y-%m-%d")

def recalculate_frequency(freq, full = False) -> int:
    if not full:
        if freq[-1].lower() == 'd':
            k = int(freq[:-1])
        elif freq[-1].lower() == 'w':
            k = int(freq[:-1])*5
        elif freq[-1].lower() == 'm':
            k = int(freq[:-1])*22
        elif freq[-1].lower() == 'y':
            k = int(freq[:-1])*252
    else:
        if freq[-1].lower() == 'd':
            k = int(freq[:-1])
        elif freq[-1].lower() == 'w':
            k = int(freq[:-1])*7
        elif freq[-1].lower() == 'm':
            k = int(freq[:-1])*30
        elif freq[-1].lower() == 'y':
            k = int(freq[:-1])*365
    return k

def generate_start_end(end: str, freq: str, len_train: int = 2) -> tuple[str]:
    k = recalculate_frequency(freq, full = True)
    shift = (k+1)*len_train
    start = shift_date(end, -shift)
    return (start, end)
    