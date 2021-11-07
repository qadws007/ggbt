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
class KDJ(bt.Indicator):
    lines = ('K', 'D', 'J')

    params = (
        ('period_kdj', 10),
        ('period_dfast', 3),
        ('period_dslow', 3),
    )

    plotlines = dict(
        J=dict(
            _fill_gt=('K', ('red', 0.50)),
            _fill_lt=('K', ('green', 0.50)),
        )
    )

    def __init__(self):
        self.addminperiod(int(np.max([self.params.period_kdj, self.params.period_dfast, self.params.period_dslow])) + 1)
        # Add a KDJ indicator
        self.kd = bt.indicators.StochasticFull(
            self.data,
            period=self.p.period_kdj,
            period_dfast=self.p.period_dfast,
            period_dslow=self.p.period_dslow,
        )

        self.l.K = self.kd.percD
        self.l.D = self.kd.percDSlow
        self.l.J = self.K * 3 - self.D * 2


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):
    params = (('short', 95),
              ('long', 5),
              ('period_rsi', 6),
              ('period_kdj', 9),
              ('period_dfast', 3),
              ('period_dslow', 3),
              )

    def __init__(self):
        self.addminperiod(int(np.max(
            [self.p.period_rsi, self.p.period_kdj, self.p.period_dfast, self.p.period_dslow, self.p.short,
             self.p.long])) + 1)
        # 保存收盘价的引用
        self.dataclose = self.datas[0].close
        # self.rsi = bt.indicators.RSI_SMA(
        #     self.data.close, period=self.p.period_rsi, upperband=self.p.short, lowerband=self.p.long)

        self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=int(self.p.period_rsi),
                                                       upperband=int(self.p.short), lowerband=int(self.p.long))
        self.kdj = KDJ(period_kdj=int(self.p.period_kdj), period_dfast=int(self.p.period_dfast),
                       period_dslow=int(self.p.period_dslow))
        self.kdjsignal = bt.indicators.CrossOver(self.kdj.l.J, self.kdj.l.K)

    def next(self):
        if not self.position:
            if self.rsi < self.params.short and self.kdjsignal == 1:
                self.order = self.buy()
        else:
            if self.rsi > self.params.long and self.kdjsignal == -1:
                self.order = self.sell()



    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        if not trade.isclosed:
            return


# 显示所有列
pd.set_option('display.max_columns', None)
# pd.set_option('max_colwidth',50)  # 只显示50个
# 创建交易数据集
data = pd.read_csv(path_root + "/datas/47.csv", dtype='str')
data['datetime'] = data['日期'] + " " + data['时间']
data['datetime'] = pd.to_datetime(data['datetime'])
data.index = data['datetime']
data.drop(['结算价', 'datetime', '日期', '时间'], axis=1, inplace=True)
print(data)





back_year = 2
end = dt.datetime.now()
sta = dt.datetime.now() - dt.timedelta(days=back_year * 30)
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
def runstrat(period_rsi, short, long, period_kdj, period_dslow, period_dfast):
    global times
    print('I am called %s ,第 %s 次.' % (datetime.now().strftime('%H:%M:%S'), times))
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy, period_rsi=period_rsi, short=short, long=long, period_kdj=period_kdj,
                        period_dslow=period_dslow, period_dfast=period_dfast)
    cerebro.adddata(data)
    cerebro.addsizer(bt.sizers.AllInSizer)
    cerebro.broker.setcash(1000000.0)  # 设置初始资金
    cerebro.run()
    times=times+1
    return cerebro.broker.getvalue()


opt = optunity.maximize(runstrat, num_evals=399, solver_name='particle swarm',
                        period_rsi=[5, 12], short=[1, 100], long=[1, 100],
                        period_kdj=[5, 12], period_dslow=[2, 9], period_dfast=[2, 9])

########################################

# 优化完成，得到最优参数结果
optimal_pars, details, _ = opt
print('Optimal Parameters:')
print('period_rsi = %.2f' % optimal_pars['period_rsi'])
print('short = %.2f' % optimal_pars['short'])
print('long = %.2f' % optimal_pars['long'])
print('period_kdj = %.2f' % optimal_pars['period_kdj'])
print('period_dfast = %.2f' % optimal_pars['period_dfast'])
print('period_dslow = %.2f' % optimal_pars['period_dslow'])
# 利用最优参数最后回测一次，作图
cerebro = bt.Cerebro()
cerebro.addstrategy(TestStrategy,
                    period_rsi=optimal_pars['period_rsi'], short=optimal_pars['short'],
                    long=optimal_pars['long'], period_kdj=optimal_pars['period_kdj'],
                    period_dslow=optimal_pars['period_dslow'], period_dfast=optimal_pars['period_dfast'])
cerebro.adddata(data)
cerebro.run()
print(cerebro.broker.getvalue() + cerebro.broker.getcash())
cerebro.plot()
