import pyefun.wxefun as wx

on_off = False
last_warning = (0,None)

import threading
import sched
import time

s = sched.scheduler(time.time, time.sleep)


class 窗口1(wx.窗口):
    def __init__(self):
        self.初始化界面()

    def 初始化界面(self):
        #########以下是创建的组件代码#########
        wx.窗口.__init__(self, None, title='蝈蝈行情预警系统', size=(595, 390), name='frame',
                       style=wx.窗口边框.普通可调边框 & ~(wx.窗口样式.最大化按钮))
        self.容器 = wx.容器(self)
        self.Centre()
        self.窗口1 = self

        self.窗口1.背景颜色 = (171, 171, 171, 255)
        self.按钮1 = wx.按钮(self.容器, size=(81, 42), pos=(53, 286), label='开始执行')
        self.按钮1.绑定事件(wx.事件.被单击, self.按钮1_被单击)
        self.按钮2 = wx.按钮(self.容器, size=(81, 42), pos=(375, 286), label='关闭')
        self.按钮2.绑定事件(wx.事件.被单击, self.按钮2_被单击)
        self.选择框1 = wx.选择框(self.容器, size=(60, 30), pos=(188, 13), label='1分钟', style=wx.CHK_2STATE)
        self.选择框1.标题居左 = False
        self.选择框1.选中 = False
        self.选择框2 = wx.选择框(self.容器, size=(60, 30), pos=(188, 49), label='5分钟', style=wx.CHK_2STATE)
        self.选择框2.标题居左 = False
        self.选择框2.选中 = False
        self.选择框3 = wx.选择框(self.容器, size=(60, 30), pos=(188, 85), label='15分钟', style=wx.CHK_2STATE)
        self.选择框3.标题居左 = False
        self.选择框3.选中 = False
        self.选择框4 = wx.选择框(self.容器, size=(60, 30), pos=(188, 122), label='30分钟', style=wx.CHK_2STATE)
        self.选择框4.标题居左 = False
        self.选择框4.选中 = False
        self.选择框5 = wx.选择框(self.容器, size=(60, 30), pos=(188, 158), label='60分钟', style=wx.CHK_2STATE)
        self.选择框5.标题居左 = False
        self.选择框5.选中 = False
        self.选择框6 = wx.选择框(self.容器, size=(60, 30), pos=(188, 194), label='日线', style=wx.CHK_2STATE)
        self.选择框6.标题居左 = False
        self.选择框6.选中 = False
        self.选择框7 = wx.选择框(self.容器, size=(60, 30), pos=(188, 231), label='周线', style=wx.CHK_2STATE)
        self.选择框7.标题居左 = False
        self.选择框7.选中 = False
        self.编辑框1 = wx.编辑框(self.容器, size=(150, 222), pos=(18, 35), value='',
                           style=wx.TE_LEFT | wx.TE_MULTILINE | wx.HSCROLL)
        self.编辑框1.背景颜色 = (255, 255, 255, 255)
        self.标签1 = wx.标签(self.容器, size=(100, 18), pos=(17, 15), label='预警的代码：', style=wx.ALIGN_CENTER)
        self.编辑框2 = wx.编辑框(self.容器, size=(303, 222), pos=(261, 35), value='',
                           style=wx.TE_LEFT | wx.TE_MULTILINE | wx.HSCROLL)
        self.编辑框2.背景颜色 = (255, 255, 255, 255)
        self.按钮3 = wx.按钮(self.容器, size=(81, 42), pos=(205, 286), label='停止执行')
        self.按钮3.绑定事件(wx.事件.被单击, self.按钮3_被单击)

    #########以上是创建的组件代码##########

    #########以下是组件绑定的事件代码#########

    def 按钮2_被单击(self, event):
        api.disconnect()
        app.ExitMainLoop()

    def 按钮1_被单击(self, event):
        count_down_start(self)

    def 按钮3_被单击(self, event):
        on_off = False

    #########以上是组件绑定的事件代码#########


class 应用(wx.App):
    def OnInit(self):
        self.窗口1 = 窗口1()
        self.窗口1.Show(True)
        print('这才是窗口创建完毕！')
        return True


import time


def count_down_start(窗口1):
    # 窗口1.编辑框2.加入文本("倒计时3秒，准备开始！\n")
    # for i in range(3):
    #     窗口1.编辑框2.加入文本(str(3 - i) + "\n")
    #     time.sleep(1)
    窗口1.编辑框2.加入文本("开始监控！\n")
    on_off = True
    while on_off == True:
        # IND.kdj(IND, get_today_data('510050', 1))
        kdjw = IND()
        df = kdjw.kdj(get_today_data('510050', 1))
        # print(df)
        warning(df)
        time.sleep(1.5)


import pandas as pd
# 显示所有列
# pd.set_option('display.max_columns', None)
from pytdx.hq import TdxHq_API


def text(t):
    a = 窗口1()
    a.编辑框2.加入文本(t + "\n\n")


import winsound


def warning(df):
    last_cross = df['cross'][-1:].values[0]
    # print(last_cross)
    if last_cross == 0:

        return
    if last_cross == 1:
        global last_warning
        t1 = df.index[-1:].values[0]
        if last_warning[0] != 1 or last_warning[1] !=t1:
            j = df['slowj'][-1:].values[0]
            c = df['cross'][-1:].values[0]
            text(t=str(t1)[:19] + "\n" + "J值: %.2f  方向: %.2f" % (j, c))
            print(str(t1)[:19] + "\n" + "J值: %.2f  方向: %.2f" % (j, c))
            print("last_warning: " + str(last_warning))
            last_warning = (1,t1)
            winsound.Beep(900, 1500)

    elif last_cross == -1:
        t1 = df.index[-1:].values[0]
        if last_warning[0] != -1 or last_warning[1] !=t1:

            j = df['slowj'][-1:].values[0]
            c = df['cross'][-1:].values[0]
            text(t=str(t1)[:19] + "\n" + "J值: %.2f  方向: %.2f" % (j, c))
            print(str(t1)[:19] + "\n" + "J值: %.2f  方向: %.2f" % (j, c))
            print("last_warning: " + str(last_warning))
            last_warning = (-1,t1)
            winsound.Beep(300, 1500)

    t1 = df.index[-1:].values[0]
    j = df['slowj'][-1:].values[0]
    c = df['cross'][-1:].values[0]
    print(str(t1)[:19] + "\n" + "J值: %.2f  方向: %.2f" % (j, c))
    print("last_warning: " + str(last_warning))
    pass


#api = TdxHq_API(heartbeat=True, auto_retry=True)
api = TdxHq_API()
# if api.connect('119.147.212.81', 7709):
#     print(2333)
#     api.disconnect()


def decorator_connect(func):
    def wrapper(*args, **kwargs):
        with api.connect('119.147.212.81', 7709):
            return func(*args, **kwargs)
    return wrapper


@decorator_connect
def get_today_data(code, market):
    data = api.get_security_bars(7, market, code, 0, calc_time())
    if data==None:
        api.disconnect()
        return exit()
    print(data)
    data = api.to_df(data)
    data.index = pd.to_datetime(data['datetime'])
    data.drop(['year', 'month', 'day', 'hour', 'minute', 'datetime'], axis=1, inplace=True)
    # print(data)
    return data


@decorator_connect
def get_now_data():
    pass


import datetime


def calc_time():
    now = datetime.datetime.now()
    t1 = datetime.timedelta(hours=now.hour, minutes=now.minute) - datetime.timedelta(hours=9, minutes=30)
    if t1.days < 0:
        rt = 249
        print("未开盘")
    elif t1 < datetime.timedelta(hours=2):
        rt = divmod(t1.seconds, 60)[0] + 9
    elif datetime.timedelta(hours=3.5) > t1 >= datetime.timedelta(hours=2):
        rt = 128
    elif datetime.timedelta(hours=3.5) <= t1 < datetime.timedelta(hours=5.5):
        rt = divmod(t1.seconds - 1.5 * 3600, 60)[0] + 9
    elif t1 > datetime.timedelta(hours=5.5):
        rt = 249
    print(rt)
    return rt


import talib
import matplotlib.pyplot as plt


class IND:

    def kdj(self, df):
        # KDJ 值对应的函数是 STOCH
        df['slowk'], df['slowd'] = talib.STOCH(
            df['high'].values,
            df['low'].values,
            df['close'].values,
            fastk_period=9,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0)
        # 求出J值，J = (3*K)-(2*D)
        df['slowj'] = list(map(lambda x, y: 3 * x - 2 * y, df['slowk'], df['slowd']))
        df['cross'] = pd.DataFrame(self.crossover(df['slowj'], df['slowk'])).values
        print(df[-5:])
        return df

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
    app = 应用()
    app.MainLoop()
