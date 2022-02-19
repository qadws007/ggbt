import akshare as ak
import os.path
import datetime as dt

# 获取根目录
import pandas as pd

path_root = os.path.dirname(os.getcwd())


def list_stock_ak():
    df = ak.stock_zh_a_spot_em()
    df[['代码', '名称']].to_csv(path_root + r"\datas\list_stock_ak.csv")


def list_fund_ak():
    df = ak.fund_em_fund_name()
    df.to_csv(path_root + r"\datas\list_fund_ak.csv")


def list_index_ak():
    df = ak.stock_zh_index_spot()
    df[['代码', '名称']].to_csv(path_root + r"\datas\list_index_ak.csv")


def get_stock_daily_ak(code=None, start_date=None, end_date=None):
    if start_date is None or end_date is None:
        end = dt.datetime.now().strftime("%Y%m%d")
        sta = dt.datetime.now()

        sta = sta.replace(
            #year=sta.year-1 if sta.month > 1 else sta.year,
            month=sta.month - 6 if sta.month > 6 else sta.month
        )
        sta = sta.strftime("%Y%m%d")



    if code:
        for i in range(len(code)):
            df = ak.stock_zh_a_hist(symbol=code, start_date=sta, end_date=end, adjust="qfq")
            #df = ak.stock_zh_a_hist(symbol=code, adjust="qfq")
            if type(df):
                df.to_csv(path_root + r"\datas\%s.csv" % code)
            else:
                print("获取数据异常！")


def get_fund_daily_ak(code=None, start_date=None, end_date=None):
    if start_date is None or end_date is None:
        end = dt.datetime.now().strftime("%Y%m%d")
        sta = dt.datetime.now()

        sta.replace(
            # year=sta.year if sta.month > 1 else sta.year - 1,
            month=sta.month - 3 if sta.month >= 3 else sta.month
        )
        sta = sta.strftime("%Y%m%d")

    if isinstance(code,list) :
        for i in range(len(code)):
            df1 = ak.fund_em_open_fund_info(fund=code[i])

            df2 = ak.fund_em_open_fund_info(fund=code[i], indicator='同类排名走势')
            df2.rename(columns = {"报告日期": "净值日期"},inplace = True)
            df= df1.merge(df2,on='净值日期', how='left')
            if type(df2):
                print(df1)
                print(df2)
                print(df)

                # df.to_csv(path_root+r"\datas\%s.csv"%code)
            else:
                print("获取数据异常！")
    else:
        print("code 必须是个list，哪怕只有一个index")

def get_fund_minute_ak(code=None, start_date=None, end_date=None):

    pass

if __name__=='__main__':
    # list_stock_ak()
    # list_index_ak()
    get_fund_daily_ak(["510300"])
    #get_stock_daily_ak('600519')
