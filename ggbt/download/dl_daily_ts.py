from token_ts import *
import os


path_root=os.path.dirname(os.getcwd())

def get_stock_basic():
    data1 =pro.stock_basic()
    data1.to_csv(path_root + r"\datas\list_tushare.csv")

def get_stock_daily():
    df = ts.pro_bar(ts_code='000001.SZ', start_date='20180101', end_date='20181011', ma=[5, 20, 50],factors=['tor', 'vr'])


