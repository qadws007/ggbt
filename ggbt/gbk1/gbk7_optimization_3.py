from datetime import datetime
import backtrader as bt
import pandas as pd
import os.path  # 管理路径
import sys
import datetime as dt
import numpy as np
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo
import optunity

# 获取根目录
path_root = os.path.dirname(os.getcwd())


class stampDutyCommissionScheme(bt.CommInfoBase):
    '''
    本佣金模式下，买入股票仅支付佣金，卖出股票支付佣金和印花税.
    '''
    params = (
        ('stamp_duty', 0.001),  # 印花税率
        ('commission', 0.00011),  # 佣金率
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
    )

    def _getcommission(self, size, price, pseudoexec):
        '''
        If size is greater than 0, this indicates a long / buying of shares.
        If size is less than 0, it idicates a short / selling of shares.
        '''

        if size > 0:  # 买入，不考虑印花税
            re = size * price * self.p.commission * 100
            if re < 1: re = 1
            return re
        elif size < 0:  # 卖出，考虑印花税
            re = - size * price * (self.p.stamp_duty + self.p.commission * 100)
            if re < 1: re = 1
            return re
        else:
            return 0  # just in case for some reason the size is 0.


# set sizer
class LongOnly(bt.sizers.AllInSizerInt):
    params = (('percents', 99),)

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:  # 如果是买单，则下单量为self.p.stake
            size = cash / data.close[0] * (self.params.percents / 100)
            return int(size)

        # 以下处理卖单情况，先获取仓位对象
        position = self.broker.getposition(data)
        # 卖单返回的下单量，防止形成短仓
        return position.size


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):
    params = (
        ('s1', 1),
        ('s2', 2),
        ('l1', 2),
        ('l2', 1),
    )

    def __init__(self):
        self.addminperiod(int(np.max([self.params.s1, self.params.s2, self.params.l1, self.params.l2])) + 1)
        # 保存收盘价的引用
        self.s1 = bt.ind.SMA(self.data.close, period=self.params.s1)
        self.s2 = bt.ind.SMA(self.data.close, period=self.params.s2)
        self.l1 = bt.ind.SMA(self.data.close, period=self.params.l1)
        self.l2 = bt.ind.SMA(self.data.close, period=self.params.l2)
        self.signal_buy = bt.ind.CrossOver(self.s1, self.s2)
        self.signal_sell = bt.ind.CrossOver(self.l1, self.l2)

    def next(self):
        if not self.position:
            if self.signal_buy == 1:
                self.order = self.buy()

        else:
            if self.signal_sell == 1:
                self.order = self.sell()


# 显示所有列
pd.set_option('display.max_columns', None)
# 创建交易数据集
data = pd.read_csv(path_root + "/datas/f_510300_ak.csv", usecols=[1, 2, 3], header=0, names=['datetime', 'close', 'sumnet'], parse_dates=["datetime"], index_col=0)
# python 的标准库手册推荐在任何情况下尽量使用time.clock().
# 只计算了程序运行CPU的时间，返回值是浮点数
import time

start = time.perf_counter()
data = data.iloc[::-1]
end = time.perf_counter()
print('Running time: %s Seconds' % (end - start))

print(data.dtypes, data)
back_year = 2
end = dt.datetime.now()
sta = dt.datetime.now() - dt.timedelta(days=back_year * 365)
data = bt.feeds.PandasData(
    fromdate=sta,
    todate=end,
    dataname=data,
    # datetime=-1,
    open=1,
    high=1,
    low=1,
    close=1,
    volume=1,
    openinterest=-1,
)

res = pd.DataFrame()
# 评估函数，输入参数，返回评估函数值，这里是总市值，要求最大化
def run1(s1, s2, l1, l2):
    global res
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.addstrategy(TestStrategy, s1=int(s1), s2=int(s2), l1=int(l1), l2=int(l2))
    cerebro.adddata(data)
    cerebro.addsizer(LongOnly)
    comminfo = stampDutyCommissionScheme()
    cerebro.broker.addcommissioninfo(comminfo)
    startcash = 100000.0
    cerebro.broker.setcash(startcash)  # 设置初始资金
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='ta')
    rs = cerebro.run()
    rs = rs[0]
    try:
        pnl = (cerebro.broker.getvalue() / startcash - 1)
        pnly = pow(pnl + 1, 1 / back_year)-1
        total = rs.analyzers.ta.rets['total']['total']
        winp = rs.analyzers.ta.rets['won']['total'] / total
        # print(cerebro.broker.getvalue(), winp)
    except:
        total = 0
        winp = 0
        print('error')
    if 0>pnly or total<10*back_year or winp<0.44:
        return
    re=pd.DataFrame([[s1,s2,l1,l2,total,winp,cerebro.broker.getvalue(),pnly]],columns=['s1','s2','l1','l2','times','win','value','pnly'])
    res=res.append(re,ignore_index=True)



def calc_zuhe(*args):
    cmbty = []
    for a in args[0]:
        for b in args[1]:
            for c in args[2]:
                for d in args[3]:
                    cmbty.append([a, b, c, d])
    return cmbty


zuhe = calc_zuhe(range(1, 21, 2), range(2, 62, 2), range(2, 62, 2), range(1, 21, 2))


for n, i in enumerate(zuhe):
    if i[1] <= i[0] or i[2] <= i[3]:
        continue
    re = run1(i[0], i[1], i[2], i[3])
    print('正在进行第：', n + 1, "/", len(zuhe))
    print(res.tail())
    print('')

res.to_csv(r'C:\Users\Administrator\Desktop\gg.csv')

