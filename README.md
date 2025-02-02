# Project description

Repo dedicated for Exchange-traded funds (ETFs) trading. The main emphasis so far has been on Markowitz-type portfolio analysis methods. Some parts of the package are based on python **PyPortfolioOpt** package:

*Martin, R. A., (2021). PyPortfolioOpt: portfolio optimization in Python. Journal of Open Source Software, 6(61), 3066, https://doi.org/10.21105/joss.03066*

Naturally, the code strongly bases on software allowing to connect with XTB via API. Two main sources are:

- [xAPI documentation](http://developers.xstore.pro/documentation/)
- repositories from [ddalgotrader](https://github.com/ddalgotrader) github account.

The project is aimed at Polish users of XTB platform. It is suited for performing calculations in PLN, including nominal and percentage returns. Currency exchange rates load automatically. 

If you want to use the package, you just have to:

- possess an account on **XTB** (real or demo)
- download the **main** branch of the repo and inside of the folder **APICommunication** add a **config.py** file:

```{python}
# config.py
user_id = 'MY_XTB_USER_ID'
pwd = 'MY_XTB_PASSWORD'
```

If you have a real XTB account, in the file **APIConnector.py** you should see:

```{python}
# APIConnector.py
...
#default connection properites
DEFAULT_XAPI_ADDRESS = 'xapi.xtb.com'

DEFAULT_XAPI_PORT           = 5112
DEFUALT_XAPI_STREAMING_PORT = 5113
...
```

If you have a demo XTB account, in the file **APIConnector.py** you should instead see:

```{python}
# APIConnector.py
...
#default connection properites
DEFAULT_XAPI_ADDRESS = 'xapi.xtb.com'

DEFAULT_XAPI_PORT           = 5124
DEFUALT_XAPI_STREAMING_PORT = 5125
...
```

Feel free to contact me directly in case you want to contribute to the package.
