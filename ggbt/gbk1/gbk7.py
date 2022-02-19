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


# KDJ indicator
class Rsimacd(bt.Indicator):
    lines = ('n1', 'n2')

    params = (
        ('short', 9),
        ('long', 19),
        ('m', 5),
        ('n', 5),
        ('k1', 1),
        ('k2', 5),
    )

    def __init__(self):
        self.addminperiod(int(np.max(
            [self.params.short, self.params.long, self.params.m, self.params.n, self.params.k1, self.params.k2])) + 2)
        # Add a KDJ indicator
        rsi = bt.ind.RSI(self.data.close, period=self.params.n)
        diff = (bt.ind.EMA(rsi, period=self.params.short) - bt.ind.EMA(rsi, period=self.params.long)) / bt.ind.EMA(rsi,
                                                                                                                   period=self.params.short)
        dea = bt.ind.EMA(diff, period=self.params.m)

        self.lines.n1 = bt.ind.EMA(diff - dea, period=self.params.k1)
        self.lines.n2 = bt.ind.EMA(diff - dea, period=self.params.k2)


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):
    params = (
        ('short', 9),
        ('long', 19),
        ('m', 5),
        ('n', 5),
        ('k1', 1),
        ('k2', 5),
    )

    def __init__(self):
        self.addminperiod(int(np.max(
            [self.params.short, self.params.long, self.params.m, self.params.n, self.params.k1, self.params.k2])) + 2)
        # 保存收盘价的引用
        self.haha = Rsimacd(short=self.p.short, long=self.p.long, m=self.p.m, n=self.p.n, k1=self.p.k1, k2=self.p.k2)
        self.signal = bt.ind.CrossOver(self.haha.n1, self.haha.n2)

    def next(self):
        if not self.position:
            if self.signal == 1:
                self.order = self.buy()
        else:
            if self.signal == -1:
                self.order = self.sell()



# 显示所有列
pd.set_option('display.max_columns', None)
# 创建交易数据集
data = pd.read_csv(path_root + "/datas/47.csv", dtype='str')
data['datetime'] = data['日期'] + " " + data['时间']
data['datetime'] = pd.to_datetime(data['datetime'])
data.index = data['datetime']
data.drop(['结算价', 'datetime', '日期', '时间'], axis=1, inplace=True)
print(data)





back_year = 1
end = dt.datetime.now()
sta = dt.datetime.now() - dt.timedelta(days=back_year * 180)
data[['开盘', '最高', '最低', '收盘', '成交量']] = data[['开盘', '最高', '最低', '收盘', '成交量']].astype('float')
data = bt.feeds.PandasData(
    fromdate=sta,
    todate=end,
    dataname=data,
    # datetime=-1,
    open=0,
    high=1,
    low=2,
    close=3,
    volume=4,
    openinterest=-1,
)

# cerebro = bt.Cerebro(tradehistory=True)
# # 加载策略
# cerebro.addstrategy(strategy=TestStrategy,period_rsi=10)
# # 加载交易数据
# cerebro.adddata(data, name="ok")
# cerebro.addsizer(LongOnly)
# # cerebro.addobserver(bt.observers.Broker)
# # cerebro.addobserver(bt.observers.Trades)
#
# startcash = 1000000
# cerebro.broker.setcash(startcash)
# # 防止下单时现金不够被拒绝。只在执行时检查现金够不够。
# cerebro.broker.set_checksubmit(False)
# comminfo = stampDutyCommissionScheme()
# cerebro.broker.addcommissioninfo(comminfo)
#
# results = cerebro.run()
# cerebro.plot()

times = 1


# 评估函数，输入参数，返回评估函数值，这里是总市值，要求最大化
def runstrat(short, long,m,n,k1,k2):
    global times
    print('I am called %s ,第 %s 次.' % (datetime.now().strftime('%H:%M:%S'), times))
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy, short=int(short),long=int(long),m=int(m),n=int(n),k1=int(k1),k2=int(k2))
    cerebro.adddata(data)
    cerebro.addsizer(LongOnly)
    comminfo = stampDutyCommissionScheme()
    cerebro.broker.addcommissioninfo(comminfo)
    cerebro.broker.setcash(100000.0)  # 设置初始资金
    cerebro.run()
    times=times+1
    return cerebro.broker.getvalue()


opt = optunity.maximize(runstrat, num_evals=3, solver_name='particle swarm',
                        short=[2, 20], long=[2, 40],
                        m=[2,15],n=[2,15],k1=[1,5],k2=[2,15])

########################################

# 优化完成，得到最优参数结果
optimal_pars, details, _ = opt
#print(opt)

print('Optimal Parameters:')

print('short = %.2f' % optimal_pars['short'])
print('long = %.2f' % optimal_pars['long'])
print('m = %.2f' % optimal_pars['m'])
print('n = %.2f' % optimal_pars['n'])
print('k1 = %.2f' % optimal_pars['k1'])
print('k2 = %.2f' % optimal_pars['k2'])
# 利用最优参数最后回测一次，作图
cerebro = bt.Cerebro()
print(optimal_pars)
for i in optimal_pars:
    optimal_pars[i]=int(optimal_pars[i])
cerebro.addstrategy(TestStrategy,
                    m=optimal_pars['m'], short=optimal_pars['short'],
                    long=optimal_pars['long'], n=optimal_pars['n'],
                    k1=optimal_pars['k1'], k2=optimal_pars['k2'])
cerebro.adddata(data)
cerebro.addsizer(bt.sizers.AllInSizer)
comminfo = stampDutyCommissionScheme()
cerebro.broker.addcommissioninfo(comminfo)
cerebro.broker.setcash(100000.0)  # 设置初始资金
cerebro.run()
print(cerebro.broker.getvalue())
cerebro.plot()
