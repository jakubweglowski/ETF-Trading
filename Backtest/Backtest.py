import pandas as pd

import APICommunication.config as cfg
from Data.DataLoader import *
from Data.DataCleaner import *
from MarkowitzAnalysis.ReturnAnalysis import *

class Backtest:
    
    def __init__(self, start: str, end: str, freq: str, len_train: int):
        self.start = start
        self.end = end
        self.freq = freq
        self.len_train = len_train + 1
        
    def generate_train_test(self):
        
        dates = [x.strftime("%Y-%m-%d") for x in pd.date_range(self.start, self.end, freq=self.freq)]

        train = []
        test = []
        for i, x in enumerate(dates):
            
            if i+self.len_train+1 >= len(dates):
                break
            
            start_train = dates[i]
            end_train = dates[i+self.len_train]
            end_test = dates[i+self.len_train+1]
            
            train.append((start_train, end_train))
            test.append((end_train, end_test))

        assert len(train) == len(test)
        
        return train, test
    
    def getSummary(self,
                   sharpe_threshold: float = 1.5,
                   low_CI_threshold: float = 1.5):
        
        train, test = self.generate_train_test()
        
        summary_dict = {}

        for i in range(len(train)):
            
            # Okres treningowy
            start_train, end_train = train[i]
            
            # Okres testowy
            start_test, end_test = test[i]
            
            # Ładujemy całe dane na raz
            dataloader = DataLoader(cfg.user_id, cfg.pwd)
            
            print(f"[INFO] Okres {i+1} z {len(train)}. Pobieramy dane od {start_train} do {end_test}: {now(False)}")
            data = dataloader.loadInstrumentsData(start_train, end_test)
            info = dataloader.loadInstrumentsInfo()
            
            datacleaner = DataCleaner(data, info, verbose=False)
            returnRates = datacleaner.getReturnRates(self.freq)
            
            # Trening
            print(f"\t[INFO] Trening w okresie od {start_train} do {end_train}")

            train_indices = returnRates.index.isin(pd.date_range(start_train, end_train))
            mo = MarkowitzOptimization(returnRates.loc[train_indices, :], self.freq, verbose=False)
            mo.getOptimalWeights(model='max_sharpe', risk_method='oas')
            pp = mo.getPortfolio()
            expected_return = pp.portfoliomean
            conf_int = getQuantiles(pp.portfolioReturn, q=0.05)
            sharpe_ratio = pp.sharpe_ratio
            
            print(f"\tOczekiwany zwrot treningowy: {expected_return:.2%}")
            print(f"\tSharpe Ratio: {sharpe_ratio:.2f}")
            print()
            portfolio = pp.portfolio
            
            # Test
            print(f"\t[INFO] Test w okresie od {start_test} do {end_test}")

            test_indices = returnRates.index.isin(pd.date_range(start_train, end_train))
            pp = PortfolioPerformance(portfolio, returnRates.loc[test_indices, :], self.freq, 'empirical',)
            true_return = pp.portfolioReturn.iloc[-1]
            
            # if sharpe_ratio >= 1.0:
            #     if true_return < conf_int[0]: summary_dict['below'] += 1
            #     elif (true_return >= conf_int[0]) and (true_return < expected_return): summary_dict['lower_half'] += 1
            #     elif (true_return >= expected_return) and (true_return < conf_int[1]): summary_dict['upper_half'] += 1
            #     elif true_return > conf_int[1]: summary_dict['above'] += 1
            #     else: print('Jakiś idiotyczny błąd xd')
            
            print(f"\tRzeczywisty zwrot w okresie testowym: {true_return:.2%}")
            print(f"\tTreningowy przedział ufności: [{conf_int[0]:.2%}, {conf_int[1]:.2%}]")
            print()
            
            summary_dict[i+1] = {'ExpectedReturn': round(100*expected_return, 2),
                                 'ConfIntLow': round(100*conf_int[0], 2),
                                 'ConfIntHigh': round(100*conf_int[1], 2),
                                 'SharpeRatio': sharpe_ratio,
                                 'TrueReturn': round(100*true_return, 2)}

        summary = pd.DataFrame(summary_dict).T
        summary['Error'] = (summary['TrueReturn'] - summary['ExpectedReturn'])
        summary['InConfInt'] = summary['TrueReturn'].between(summary['ConfIntLow'], summary['ConfIntHigh'])
        summary['WasOpened'] = (summary['SharpeRatio'] > sharpe_threshold) & (summary['ConfIntLow'] > low_CI_threshold)
        summary['WasSuccessful'] = summary['WasOpened'] & ((summary['Error'] > 0) | (summary['InConfInt']))
        
        return summary
    
    