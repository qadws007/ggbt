from datetime import datetime
import backtrader as bt
import pandas as pd
import os.path  # 管理路径
import datetime as dt
import numpy as np

# 获取根目录
path_root = os.path.dirname(os.getcwd())


class stampDutyCommissionScheme(bt.CommInfoBase):
    '''
    本佣金模式下，买入股票仅支付佣金，卖出股票支付佣金和印花税.
    '''
    params = (
        ('stamp_duty', 0.001),  # 印花税率
        ('commission', 0.00012),  # 佣金率
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
    )

    def _getcommission(self, size, price, pseudoexec):
        '''
        If size is greater than 0, this indicates a long / buying of shares.
        If size is less than 0, it idicates a short / selling of shares.
        '''

        if size > 0:  # 买入，不考虑印花税
            return size * price * self.p.commission * 100
        elif size < 0:  # 卖出，考虑印花税
            return - size * price * (self.p.stamp_duty + self.p.commission * 100)
        else:
            return 0  # just in case for some reason the size is 0.


# set sizer
class LongOnly(bt.sizers.AllInSizerInt):
    params = (('percents', 33),)

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


# 创建策略
class factor(bt.Strategy):
    '''
    布林线均值回归策略

    进入标准:
        - 长仓:
            - 收盘价低于下轨
            - 创建Stop买单， 当价格向上突破下轨时，买入
        - 短仓（允许做空）:
            - 收盘价高于上轨
            - 创建Stop卖单， 当价格向下突破上轨时，卖出
    退出标准
        - 长/短: 价格触及中线
    '''

    params = dict(
        selcperc=0.10,  # 股票池中挑选标的股票的比例
        rperiod=1,  # 收益率计算期数, 默认1期，即月度收益率
        vperiod=36,  # 波动率计算回看期数
        mperiod=12,  # 动量指标计算回看期数
        reserve=0.05  # 5% 预留资本
    )

    def log(self, txt):
        ''' Logging function for this strategy'''
        dt = self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.rsi_5 = [bt.ind.RSI_EMA(d, period=5, plot=False) for d in self.datas if len(d.array) > 5]
        self.rsi_15 = [bt.ind.RSI_EMA(d, period=15, plot=False) for d in self.datas if len(d.array) > 15]
        self.rsi_30 = [bt.ind.RSI_EMA(d, period=30, plot=False) for d in self.datas if len(d.array) > 30]
        self.rsi_60 = [bt.ind.RSI_EMA(d, period=60, plot=False) for d in self.datas if len(d.array) > 60]
        self.rsi_d = [bt.ind.RSI_EMA(d, period=60 * 4) for d in self.datas if len(d.array) > 60 * 4]
        self.rsi_w = [bt.ind.RSI_EMA(d, period=60 * 4 * 5, plot=False) for d in self.datas if len(d.array) > 60 * 4 * 5]
        self.ma_5 = [bt.ind.SMA(d, period=5) for d in self.datas]
        self.ma_15 = [bt.ind.SMA(d, period=15) for d in self.datas]
        self.ma_30 = [bt.ind.SMA(d, period=30) for d in self.datas]
        self.ma_60 = [bt.ind.SMA(d, period=60) for d in self.datas]
        self.ma_d = [bt.ind.SMA(d, period=60 * 4) for d in self.datas]
        self.ma_w = [bt.ind.SMA(d, period=60 * 4 * 5) for d in self.datas]
        self.dp = [d for d in self.datas if len(d) > 60 * 4 * 5]

        #1、持仓额度分配
        self.cashpercentage = (1 - 0.02) / len(self.datas)



    def next(self):
        pass



    def notify_trade(self, trade):
        if trade.isclosed:
            dt = self.data.datetime.date()

            print(
                '---------------------------- TRADE ---------------------------------'
            )
            print("1: d Name:                            {}".format(
                trade.data._name))
            print("2: Bar Num:                              {}".format(
                len(trade.data)))
            print("3: Current date:                         {}".format(dt))
            print('4: Status:                               Trade Complete')
            print('5: Ref:                                  {}'.format(
                trade.ref))
            print('6: PnL:                                  {}'.format(
                round(trade.pnl, 2)))
            print(
                '--------------------------------------------------------------------'
            )

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            return

        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            if order.isbuy():
                str = '股票:%s, 已买入:%.2f, 数量:%.2f, 价值:%.2f, 手续费:%.2f' % (
                    order.data._name, order.executed.price, order.executed.size, order.executed.value,
                    order.executed.comm)
                self.log(str)

            elif order.issell():
                str = '股票:%s, 已卖出:%.2f, 数量:%.2f, 价值:%.2f, 手续费:%.2f' % (
                    order.data._name, order.executed.price, order.executed.size, order.executed.value,
                    order.executed.comm)
                self.log(str)
            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            str = "\nsize:%f\nvalue:%f\ncash:%f" % (order.executed.size, order.executed.value, order.executed.cash)
            # self.log('订单取消/保证金不足/拒绝'+str)

        # 其他状态记录为：无挂起订单
        self.order = None


cerebro = bt.Cerebro()
time0 = datetime.now()

filename = os.listdir(path_root + "/datas/hs300m")
maxstocknum = 2  # 股票池最大股票数目
# filename=filename[1971:1972]
# filename=filename[862:863]
filename = filename[0:maxstocknum]
# 设置测试时间
# back_year = 3
# end = dt.datetime.now()
# sta = dt.datetime.now() - dt.timedelta(days=back_year * 365)
i = 0
# 显示所有列
pd.set_option('display.max_columns', None)

for fname in filename:
    # 创建交易数据集
    df = pd.read_csv(path_root + "/datas/hs300m/" + fname, dtype='str', encoding="gbk", skiprows=[0, 1], skipfooter=1,
                     names=['datetimes', 'times', 'open', 'high', 'low', 'close', 'volume', 'amount'])
    df['datetime'] = df['datetimes'] + " " + df['times']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.index = df['datetime']
    df.drop(['datetime', 'datetimes', 'times', 'amount', 'volume'], axis=1, inplace=True)
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype('float')
    # print(df)
    # print(df.dtypes)
    # 排除新股
    if df.shape[0] < 60 * 4 * 5 + 1:
        print("此条为新股", fname, i)
        i = i + 1
        continue

    # 转换某些股票含时区，再选取时间区间，然后再判断行高。
    # print(df,df.dtypes)
    # df['datetimes'] = df['datetimes'].dt.tz_localize(None)
    # df = df.loc[df['datetimes'] > sta]

    # # 排除新股
    # if df.shape[0] < 22:
    #     print("此条为新股", fname, i)
    #     i = i + 1
    #     continue

    if df.iloc[0:60 * 4 * 5 + 1, 1].sum == None:
        df.iloc[0] = df.loc[df['open'] != None].ilco[0]
        print("此条开头全是空")

    data = bt.feeds.PandasData(
        fromdate=datetime(2021, 5, 6),
        dataname=df,
        open=0,
        high=1,
        low=2,
        close=3,
        volume=-1,
        openinterest=-1,
    )
    cerebro.adddata(data, name=fname)

    print("注入数据", fname, i)
    i = i + 1

# 注入策略
cerebro.addstrategy(factor)
# cerebro.optstrategy(SmaCross,pfast=range(1,20,2),pslow=range(5,40,4))

# 设置现金
startcash = 100000
cerebro.broker.setcash(startcash)
# 防止下单时现金不够被拒绝。只在执行时检查现金够不够。
cerebro.broker.set_checksubmit(False)
comminfo = stampDutyCommissionScheme()
cerebro.broker.addcommissioninfo(comminfo)
cerebro.addsizer(LongOnly)

cerebro.run()

# 最终收益或亏损
pnl = (cerebro.broker.get_value() - startcash) / startcash
print('Profit ... or Loss: {:.2f}'.format(pnl))
print("用时：", datetime.now() - time0)
cerebro.plot(volume=False)
