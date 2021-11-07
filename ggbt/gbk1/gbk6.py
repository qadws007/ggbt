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

    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

    def stop(self):
        b = 'short %.2f,long %.2f,m %.2f,n %.2f,k1 %.2f,k2 %.2f,value %.2f'
        a = '%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f' % (
            self.params.short, self.params.long, self.params.m, self.params.n, self.params.k1, self.params.k2,
            self.broker.getvalue())
        # print(a)


if __name__ == '__main__':
    # 显示所有列
    # pd.set_option('display.max_columns', None)
    # 创建交易数据集
    data = pd.read_csv(path_root + "/datas/47#IFL0.csv", dtype='str', encoding="gbk")
    data['datetime'] = data['日期'] + " " + data['时间']
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.index = data['datetime']
    data.drop(['结算价', 'datetime', '日期', '时间'], axis=1, inplace=True)
    print("加载数据完毕")

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

    cerebro = bt.Cerebro(maxcpus=1)

    # 加载交易数据
    cerebro.adddata(data, name="ok")
    cerebro.addsizer(bt.sizers.AllInSizer)
    # cerebro.addobserver(bt.observers.Broker)
    # cerebro.addobserver(bt.observers.Trades)
    startcash = 100000
    cerebro.broker.setcash(startcash)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")

    # 加载策略
    start = cerebro.optstrategy(TestStrategy,
                                short=range(5, 20, 4),
                                long=range(15, 30, 5),
                                m=range(3, 10, 4),
                                n=range(3, 10, 4),
                                k1=range(1, 10, 3),
                                k2=range(3, 20, 4),
                                )

    # short = [9,12],
    # long = [19,26],
    # m = [5],
    # n = [5],
    # k1 = [1],
    # k2 = [5,6],

    # short = range(5, 20, 4),
    # long = range(15, 30, 5),
    # m = range(3, 10, 4),
    # n = range(3, 10, 4),
    # k1 = range(1, 10, 3),
    # k2 = range(3, 20, 4),

    # cerebro.addstrategy(TestStrategy)

    rs = cerebro.run()

    par_list = [[x[0].params.short,
                 x[0].params.long,
                 x[0].params.m,
                 x[0].params.n,
                 x[0].params.k1,
                 x[0].params.k2,
                 0 if x[0].analyzers.ta.rets is None else x[0].analyzers.ta.rets.get('pnl').get(
                     'gross').get('total'),
                 0 if x[0].analyzers.ta.rets is None else x[0].analyzers.ta.rets.get('won').get('total') / (
                         x[0].analyzers.ta.rets.get('won').get('total') + x[0].analyzers.ta.rets.get('lost').get(
                     'total')) * 100,
                 ] for x in rs]

    par_df = pd.DataFrame(par_list, columns=['short', 'long', 'm', 'n', 'k1', 'k2', 'value', 'sl'])

    # print(par_df)
    # max_value=par_df.loc[par_df['value']==par_df['value'].max]
    max_value = par_df[par_df['value'] == par_df['value'].max()]
    max_value = max_value[max_value['sl'] == max_value['sl'].max()]
    max_value = max_value.iloc[0].astype("int")
    max_sl = par_df[par_df['sl'] == par_df['sl'].max()]
    max_sl = max_sl[max_sl['value'] == max_sl['value'].max()]
    max_sl = max_sl.iloc[0].astype("int")

    print(max_value, max_sl)


    def max_plot(df):
        # 显示所有列
        # pd.set_option('display.max_columns', None)
        # 创建交易数据集
        data = pd.read_csv(path_root + "/datas/47#IFL0.csv", dtype='str', encoding="gbk")
        data['datetime'] = data['日期'] + " " + data['时间']
        data['datetime'] = pd.to_datetime(data['datetime'])
        data.index = data['datetime']
        data.drop(['结算价', 'datetime', '日期', '时间'], axis=1, inplace=True)
        print("加载数据完毕")

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

        cerebro = bt.Cerebro(tradehistory=True)

        # 加载交易数据
        cerebro.adddata(data, name="ok")
        startcash = 100000
        cerebro.broker.setcash(startcash)

        # 加载策略
        cerebro.addstrategy(TestStrategy,
                            short=df['short'],
                            long=df['long'],
                            m=df['m'],
                            n=df['n'],
                            k1=df['k1'],
                            k2=df['k2'],
                            )
        cerebro.run()
        cerebro.plot()


    max_plot(max_value)
