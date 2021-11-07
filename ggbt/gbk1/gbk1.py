from datetime import datetime
import backtrader as bt
import pandas as pd
import os.path  # 管理路径
import sys
import datetime as dt
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo

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
        ('period', 9),
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
        self.addminperiod(self.params.period)
        # Add a KDJ indicator
        self.kd = bt.indicators.StochasticFull(
            self.data,
            period=self.p.period,
            period_dfast=self.p.period_dfast,
            period_dslow=self.p.period_dslow,
        )

        self.l.K = self.kd.percD
        self.l.D = self.kd.percDSlow
        self.l.J = self.K * 3 - self.D * 2

# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):
    params = (('short', 20),
              ('long', 80),)

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保存收盘价的引用
        self.addminperiod(10)
        self.dataclose = self.datas[0].close
        self.rsi = bt.indicators.RSI_SMA(
            self.data.close, period=6, upperband=80, lowerband=20)
        self.kdj=KDJ()
        self.kdjsignal=bt.indicators.CrossOver(self.kdj.l.J,self.kdj.l.K)

    def signal(self):
        #sig=self.rsi
        #self.sizer.setsizing(percents=100)

        if self.rsi > self.params.long and self.kdjsignal==-1:
            self.log('卖出, %.2f' % self.dataclose[0])
            self.order = self.sell()

        if self.rsi < self.params.short and self.kdjsignal==1:
            self.log('买入, %.2f' % self.dataclose[0])
            self.order = self.buy()
        pass


    def next(self):
        self.signal()




    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            return

        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '已买入, %.2f' % order.executed.price + ' 数量, %.2f' % order.executed.size + ' 价值, %.2f' % order.executed.value + ' 手续费, %.2f' % order.executed.comm)
                print(order.executed)
            elif order.issell():
                self.log(
                    '已卖出, %.2f' % order.executed.price + ' 数量, %.2f' % order.executed.size + ' 价值, %.2f' % order.executed.value + ' 手续费, %.2f' % order.executed.comm)

            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            str="\nsize:%f\nvalue:%f\ncash:%f"%(order.executed.size,order.executed.value,order.executed.value)
            self.log('订单取消/保证金不足/拒绝'+str)

        # 其他状态记录为：无挂起订单
        self.order = None

    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('交易利润, 毛利润 %.2f, 净利润 %.2f, 佣金 %.2f' %
                 (trade.pnl, trade.pnlcomm, trade.commission))
        print(trade)


cerebro = bt.Cerebro(tradehistory=True)

# 创建交易数据集
data = pd.read_csv(path_root + "/datas/47#IFL0.csv", dtype='str',encoding="gbk")
data['datetime'] = data['日期'] + " " + data['时间']
data['datetime'] = pd.to_datetime(data['datetime'])
data.index = data['datetime']
data.drop(['结算价', 'datetime', '日期', '时间','成交量','持仓量'], axis=1, inplace=True)
back_year = 1
end = dt.datetime.now()
sta = dt.datetime.now() - dt.timedelta(days=back_year * 180)
data[['开盘', '最高', '最低', '收盘']] = data[['开盘', '最高', '最低', '收盘']].astype('float')
print(data)
data = bt.feeds.PandasData(
    # fromdate=sta,
    # todate=end,
    dataname=data,
    # datetime=-1,
    open=0,
    high=1,
    low=2,
    close=3,
    volume=-1,
    openinterest=-1,
)

# 加载策略
cerebro.addstrategy(strategy=TestStrategy)
# 加载交易数据
cerebro.adddata(data, name="ok")
cerebro.addsizer(LongOnly)
# cerebro.addobserver(bt.observers.Broker)
# cerebro.addobserver(bt.observers.Trades)

startcash = 1000000
cerebro.broker.setcash(startcash)
# 防止下单时现金不够被拒绝。只在执行时检查现金够不够。
cerebro.broker.set_checksubmit(False)
comminfo = stampDutyCommissionScheme()
cerebro.broker.addcommissioninfo(comminfo)
# add analyzers
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')

results = cerebro.run()
strat = results[0]
pnl = (cerebro.broker.getvalue() / startcash - 1)
pnly = pow(pnl+1, 1/back_year)
print('收益率: %.2f' % (pnl*100), '年化收益率：%.2f' % ((pnly-1)*100))
print('夏普比率:', strat.analyzers.SharpeRatio.get_analysis())
print('回撤指标:', strat.analyzers.DW.get_analysis())
b = Bokeh(style='bar', plot_mode='multi', scheme=Tradimo())
print()
cerebro.plot(b)
