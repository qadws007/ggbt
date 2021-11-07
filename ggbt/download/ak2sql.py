import akshare as ak
import datetime
import baostock as bs
import pandas as pd
import time
from sqlalchemy import create_engine
import sqlalchemy

#### 登陆系统 ####
lg = bs.login()
# 显示登陆返回信息
print('login respond error_code:' + lg.error_code)
print('login respond  error_msg:' + lg.error_msg)
# engine = create_engine("mysql://{}:{}@{}/{}?charset=utf8".format('username','password','host:port', 'database'))
engine = create_engine("mysql://{}:{}@{}/{}?charset=utf8".format('root', 'root', 'localhost:3306', 'stock_datas'))
'''
#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为200，默认为50
pd.set_option('max_colwidth',200)
'''


def a():
    df = ak.stock_zh_a_spot_em()
    df.drop('序号', axis=1, inplace=True)
    df.columns = ['code', 'name', 'close', 'zfp', 'zd', 'volume', 'amount', 'zf', 'high', 'low', 'open', 'pre_close',
                  'lb', 'hsl', 'syl_d', 'sjl']
    print(df.dtypes)
    print(df)
    df[0:5].to_sql('stock_datas_em_all', engine, index=False, if_exists='append')


def add_datas1():
    now4 = datetime.datetime.now()
    df = ak.stock_zh_a_spot_em()
    print('web时间', datetime.datetime.now() - now4)

    df.drop('序号', axis=1, inplace=True)
    df.fillna(0, inplace=True)
    df.columns = ['code', 'name', 'close', 'zfp', 'zd', 'volume', 'amount', 'zf', 'high', 'low', 'open', 'pre_close',
                  'lb', 'hsl', 'syl_d', 'sjl']
    now5 = datetime.datetime.now()

    for i in range(df.shape[0]):
        engine.execute('call add_em_all({})'.format(str(df.iloc[i].tolist())[1:-1]))
    now4 = datetime.datetime.now()
    df = ak.stock_zh_a_spot_em()
    print('写库时间', datetime.datetime.now() - now5)


# add_datas()
df0 = pd.DataFrame()


def add_datas2():
    global df0
    df = ak.stock_zh_a_spot_em()
    if df.empty:
        time.sleep(1)
        return
    df.drop('序号', axis=1, inplace=True)
    df.fillna(0, inplace=True)
    df.columns = ['code', 'name', 'close', 'zfp', 'zd', 'volume', 'amount', 'zf', 'high', 'low', 'open', 'pre_close',
                  'lb', 'hsl', 'syl_d', 'sjl']

    if df0.empty:
        print('first')
        df.to_sql('stock_datas_em_all', engine, if_exists='append', index=False)
    else:
        df1 = df.copy()
        df2 = df0.copy()
        # drop_duplicates重复数据删除
        fileds_df = df2.append(df1).drop_duplicates(keep=False)
        idx=fileds_df.groupby(['code']).apply(lambda x: x['amount'].idxmax())
        df1 =df1.iloc[idx]
        #入库
        df1.to_sql('stock_datas_em_all', engine, if_exists='append', index=False)

    df0 = df.copy()
    time.sleep(1)


def check_trade_day(day=datetime.datetime.now().date()):
    # 文本型日期
    #### 获取交易日信息 ####
    rs = bs.query_trade_dates(start_date=str(day), end_date=str(day))
    # print('query_trade_dates respond error_code:' + rs.error_code)
    # print('query_trade_dates respond  error_msg:' + rs.error_msg)

    #### 打印结果集 ####

    result = rs.get_row_data()
    # print(result)
    if result[1] == "1":
        return True
    else:
        return False


t = 0
t1 = 0
while True:

    # 判断交易时间
    now1 = datetime.datetime.now()
    now2 = datetime.timedelta(hours=now1.hour, minutes=now1.minute)
    if datetime.timedelta(hours=11, minutes=32) > now2 > datetime.timedelta(hours=9, minutes=28) or datetime.timedelta(
            hours=15, minutes=2) > now2 > datetime.timedelta(hours=12, minutes=58):
        if check_trade_day():
            # 判断交易日
            now3 = datetime.datetime.now()
            add_datas2()
            print(datetime.datetime.now() - now3, "执行了一次全网更新！")

        else:
            if t < 1:
                print(datetime.datetime.now(), "还没到交易日。")
                t = 30
            # print(t)
            time.sleep(10)
            t = t - 1

    else:
        if t1 < 1:
            print(now1, "还没到交易时间。")
            t1 = 10 ** 6
        # print(t1)
        t1 = t1 - 1


def check_table(table_name):
    check = engine.has_table(table_name)
    print(check)  # boolean
    return check


#### 登出系统 ####
bs.logout()
