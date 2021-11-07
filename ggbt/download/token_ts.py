import tushare as ts
from functools import wraps

token = "06db8cd2ea90c1a30e0ca247395e192cc795317db6ad4454fd83717d"

pro=ts.pro_api(token)



def decorator_ts_api(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """doc of wrapper"""
        ts.pro_api(token)
        return func(*args, **kwargs)
    return wrapper


