import pyefun.wxefun as wx

on_off = False
import time
import pandas as pd
import sys
import os
path_root = os.path.dirname(os.getcwd())
sys.path.append(path_root)
from datas.host import hq_hosts
# 显示所有列
# pd.set_option('display.max_columns', None)
from pytdx.hq import TdxHq_API
import winsound

import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 300)

def speke_it(words):
    engine.say(words)
    engine.runAndWait()
    engine.stop()

speke_it("好戏开场了！")

def count_down_start():

    on_off = True
    while on_off == True:
        # IND.kdj(IND, get_today_data('510050', 1))
        kdjw = IND()
        data=get_today_data('510050', 1)
        kdjw.kdj(data,1)
        kdjw.kdj(data,5)
        kdjw.kdj(data, 15)
        #kdjw.kdj(data, 30)

        time.sleep(1)

last_warning = {
    "1":[0,0],
    "5" : [0, 0],
    "15" : [0, 0],
    "30" : [0, 0],
    "60" : [0, 0],
}
def warning(df,period=1):
    global last_warning
    last_cross = df['cross'][-1:].values[0]
    # print(last_cross)
    if last_cross == 0:

        return
    if last_cross == 1:
        global last_warning
        t1 = df.index[-1:].values[0]
        if last_warning[str(period)][0] != 1 or last_warning[str(period)][1] !=t1:
            j = df['slowj'][-1:].values[0]
            c = df['cross'][-1:].values[0]
            if c == 1:
                fx = "做多"
            else:
                fx = "做空"
            print(str(t1)[:19] + "\n" + "分钟周期: %.2f  J值: %.2f  方向: %s" % (period,j, c))
            print("last_warning: last period %s ,wraning %s"%(period,last_warning[str(period)][0]) )
            winsound.Beep(900, 500)
            speke_it('周期%s,J值%i,%s' % (period, j, fx))
            last_warning[str(period)] = [1,t1]

    elif last_cross == -1:
        t1 = df.index[-1:].values[0]
        if last_warning[str(period)][0] != -1 or last_warning[str(period)][1] !=t1:

            j = df['slowj'][-1:].values[0]
            c = df['cross'][-1:].values[0]
            if c == 1:
                fx = "做多"
            else:
                fx = "做空"
            print(str(t1)[:19] + "\n" + "分钟周期: %.2f  J值: %.2f  方向: %s" % (period,j, c))
            print("last_warning: last period %s ,wraning %s"%(period,last_warning[str(period)][0]) )
            winsound.Beep(300, 500)
            speke_it('周期%s,J值%i,%s' % (period, j, fx))
            last_warning[str(period)] = [-1,t1]


    t1 = df.index[-1:].values[0]
    j = df['slowj'][-1:].values[0]
    c = df['cross'][-1:].values[0]
    if c==1:
        fx="做多"
    else:
        fx="做空"
    print(str(t1)[:19] + "\n" + "分钟周期: %.2f  J值: %.2f  方向: %s" % (period,j, fx))
    print("last_warning: last period %s ,wraning %s"%(period,last_warning[str(period)][0]) )
    speke_it('周期%s,J值%i,%s'%(period,j,fx))
    pass


# api = TdxHq_API(heartbeat=True, auto_retry=True)
api = TdxHq_API()
p = 1
def connect():
    print("start")
    global api
    global p
    if api.connect(hq_hosts[0][1], hq_hosts[0][2]):
        print('first connect')
    data = api.get_security_bars(7, 1, "510050", 0, 1)
    while data==None:
        api.disconnect()
        if api.connect(hq_hosts[p][1], hq_hosts[p][2]):
            data = api.get_security_bars(7, 1, "510050", 0, calc_time())
            print("已使用服务器：",hq_hosts[p][1], hq_hosts[p][2])
        p=p+1
        print(p)
    print("done")
    return data



def decorator_connect(func):
    def wrapper(*args, **kwargs):
        with api.connect('123.125.108.14', 7709):
            return func(*args, **kwargs)
    return wrapper



def get_today_data(code, market):
    data = api.get_security_bars(7, market, code, 0, calc_time())
    if data == None:
        data=connect()
    print(datetime.datetime.now(),"监控数据中")
    data = api.to_df(data)
    data.index = pd.to_datetime(data['datetime'])
    data.drop(['year', 'month', 'day', 'hour', 'minute', 'datetime'], axis=1, inplace=True)
    return data




@decorator_connect
def get_now_data():
    pass


import datetime


def calc_time():
    after=80
    now = datetime.datetime.now()
    t1 = datetime.timedelta(hours=now.hour, minutes=now.minute) - datetime.timedelta(hours=9, minutes=30)
    if t1.days < 0:
        rt = 240+after
        print("未开盘")
    elif t1 < datetime.timedelta(hours=2):
        rt = divmod(t1.seconds, 60)[0] + after
    elif datetime.timedelta(hours=3.5) > t1 >= datetime.timedelta(hours=2):
        rt = 120+after
    elif datetime.timedelta(hours=3.5) <= t1 < datetime.timedelta(hours=5.5):
        rt = divmod(t1.seconds - 1.5 * 3600, 60)[0] + after
    elif t1 > datetime.timedelta(hours=5.5):
        rt = 240+after
    else:
        rt = 240+after
    print(rt)
    return rt


import talib
import matplotlib.pyplot as plt


class IND:

    def kdj(self, df,period=1):
        df = df.resample(rule='%sT'%period, axis=0).mean()
        df = df.dropna(axis=0, how='any')

        #print(df[0:10])
        # KDJ 值对应的函数是 STOCH
        df['slowk'], df['slowd'] = talib.STOCH(
            df['high'].values,
            df['low'].values,
            df['close'].values,
            fastk_period=9,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0
        )
        # 求出J值，J = (3*K)-(2*D)
        df['slowj'] = list(map(lambda x, y: 3 * x - 2 * y, df['slowk'], df['slowd']))
        df['cross'] = pd.DataFrame(self.crossover(df['slowj'], df['slowk'])).values

        # print('这是 %s minute的周期的df：'%period)
        # print(df[-2:])
        return warning(df,period)

    def macd(self, df):
        df['macd'], df['macdsignal'], df['macdhist'] = talib.MACDEXT(
            df['close'],
            fastperiod=12, fastmatype=0,
            slowperiod=26, slowmatype=0,
            signalperiod=9, signalmatype=0)
        # print(df)

    def crossover(self, line1, line2):
        rt = []
        for i in range(line1.shape[0]):
            if i == 0:
                rt.append(0)
                continue
            if line1[i] > line2[i] and line1[i - 1] <= line2[i - 1]:
                rt.append(1)
            elif line1[i] < line2[i] and line1[i - 1] >= line2[i - 1]:
                rt.append(-1)
            else:
                rt.append(0)
        return rt


if __name__ == '__main__':
    connect()
    count_down_start()
    api.disconnect()
    pass