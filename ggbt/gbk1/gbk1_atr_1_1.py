from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import backtrader as bt
import os.path  # 管理路径
import sys  # 发现脚本名字(in argv[0])
import glob
from backtrader.feeds import PandasData  # 用于扩展DataFeed




class Strategy(bt.Strategy):


    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        # self.datahigh = self.datas[0].high
        # self.datalow = self.datas[0].low
        pass
        # self.order = None
        # self.buyprice = 0
        # self.buycomm = 0
        # self.newstake = 0
        # self.buytime = 0
        # # 参数计算，唐奇安通道上轨、唐奇安通道下轨、ATR
        # self.DonchianHi = bt.indicators.Highest(self.datahigh(-1), period=20, subplot=False)
        # self.DonchianLo = bt.indicators.Lowest(self.datalow(-1), period=10, subplot=False)
        # self.TR = bt.indicators.Max((self.datahigh(0)- self.datalow(0)), abs(self.dataclose(-1) -   self.datahigh(0)), abs(self.dataclose(-1)  - self.datalow(0) ))
        # self.ATR = bt.indicators.SimpleMovingAverage(self.TR, period=14, subplot=True)


##########################
# 主程序开始
#########################
cerebro = bt.Cerebro()
# cerebro = bt.Cerebro(stdstats=False)
# cerebro.addobserver(bt.observers.Broker)
# cerebro.addobserver(bt.observers.Trades)
time0=datetime.now()
# 获取根目录
path_root = os.path.dirname(os.getcwd())
filename = os.listdir(path_root+"/datas/tdx")
maxstocknum = 3  # 股票池最大股票数目
#filename=filename[1971:1972]
# filename=filename[862:863]
filename=filename[0:maxstocknum]
#设置测试时间
back_year = 1
end = datetime.now()
sta = datetime.now() - timedelta(days=back_year * 365)

for i,fname in enumerate(filename):
    df = pd.read_csv(path_root + "/datas/tdx/"+fname,
                     skiprows=[0, 1],  encoding="gbk",skipfooter =1,parse_dates=[0],
                     names=['datetimes', 'open', 'high', 'low', 'close', 'volume ', 'amount'],
                     )

    data = bt.feeds.PandasData(
        fromdate=sta,
        todate=end,
        dataname=df,
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
        #plot=False
    )

    cerebro.adddata(data,name=fname)

    print("注入数据",fname,i)


# 注入策略
cerebro.addstrategy(Strategy)
startcash = 1000000
cerebro.broker.setcash(startcash)
# 防止下单时现金不够被拒绝。只在执行时检查现金够不够。
cerebro.broker.set_checksubmit(False)
results = cerebro.run()
print('最终市值: %.2f' % cerebro.broker.getvalue())
cerebro.plot()
