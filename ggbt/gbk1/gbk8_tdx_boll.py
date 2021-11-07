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


# 创建策略
class BOLLStrat(bt.Strategy):
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

    params = (
        ("period", 20),  # 布林线周期
        ("devfactor", 1.5),  # 偏离因子
        ("size", 200),  # 订单数量
        ("debug", False)  # 是否调试
    )

    def log(self, txt):
        ''' Logging function for this strategy'''
        dt = self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.boll = [bt.indicators.BollingerBands(d,
                                                  period=self.p.period, devfactor=self.p.devfactor) for d in self.datas]
        self.cross_top = {d: bt.ind.CrossOver(d, top.lines.top, plot=False) for d, top in
                          zip(self.datas, self.boll)}
        self.cross_bot = {d: bt.ind.CrossOver(d, bot.lines.bot, plot=False) for d, bot in
                          zip(self.datas, self.boll)}
        self.cross_mid = {d: bt.ind.CrossOver(d, mid.lines.mid, plot=False) for d, mid in
                          zip(self.datas, self.boll)}

    def next(self):
        for d, boll in zip(self.datas, self.boll):
            # # 未决订单列表
            # orders = self.broker.get_orders_open(d)
            #
            # # 取消所有未决订单
            # if orders:
            #     print(orders)
            #     for order in orders:
            #         self.broker.cancel(order)
            if self.cross_bot[d]==1 :
                self.order_target_percent(  # 买入
                    exectype=bt.Order.Stop,
                    price=boll.lines.bot[0],
                    target=1/len(self.datas), data=d)

            if  self.cross_mid[d] == 1:
                self.order_target_percent(  # 买入
                    exectype=bt.Order.Stop,
                    price=boll.lines.bot[0],
                    target=1/len(self.datas)/2, data=d)

            if self.getposition(d).size > 0:
                if self.cross_top[d]==-1 :
                    self.sell(  # 买入
                        exectype=bt.Order.Stop,
                        price=boll.lines.bot[0],
                        target=self.getposition(d).size/ 2, data=d)

                if  self.cross_mid[d] == -1:
                    self.sell(  # 卖出
                        exectype=bt.Order.Stop,
                        price=boll.lines.top[0],
                        size=self.getposition(d).size, data=d)



            if self.p.debug:
                print(
                    '---------------------------- NEXT ----------------------------------'
                )
                print("1: Data Name:                            {}".format(
                    d._name))
                print("2: Bar Num:                              {}".format(
                    len(d)))
                print("3: Current date:                         {}".format(
                    d.datetime.datetime()))
                print('4: Open:                                 {}'.format(
                    d.open[0]))
                print('5: High:                                 {}'.format(
                    d.high[0]))
                print('6: Low:                                  {}'.format(
                    d.low[0]))
                print('7: Close:                                {}'.format(
                    d.close[0]))
                print('8: Volume:                               {}'.format(
                    d.volume[0]))
                print('9: Position Size:                       {}'.format(
                    self.position.size))
                print(
                    '--------------------------------------------------------------------'
                )

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
                str = '股票:%s,已买入:%.2f,数量:%.2f,价值:%.2f,手续费:%.2f,当前剩余资金:%.2f' % (
                    order.data._name, order.executed.price, order.executed.size, order.executed.value,
                    order.executed.comm,self.broker.getcash())
                self.log(str)

            elif order.issell():
                str = '股票:%s,买入价格：,卖出价格:%.2f,数量:%.2f,价值:%.2f,手续费:%.2f,当前剩余资金:%.2f' % (
                    order.data._name, order.executed.price, order.executed.size, order.executed.value,
                    order.executed.comm,self.broker.getcash())
                self.log(str)
                #self.log("现在是哪个股票：%s,现有持仓：%.2f,现在价格：%.2f,现有价值：%.2f,上次开仓价格：%.2f,当前剩余资金:%.2f"
                #         %(order.data._name,self.getposition(d).size,self.getposition(d).price,
                #           self.getposition(d).size*self.getposition(d).price,self.getposition(d).adjbase,))

            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            str = "\nsize:%f\nvalue:%f\ncash:%f" % (order.executed.size, order.executed.value, order.executed.value)
            # self.log('订单取消/保证金不足/拒绝'+str)

        # 其他状态记录为：无挂起订单
        self.order = None

def prn_obj(obj):
  print('\n'.join(['%s:%s' % item for item in obj.__dict__.items()]))

cerebro = bt.Cerebro()
time0 = datetime.now()

filename = os.listdir(path_root + "/datas/tdx")
maxstocknum = 2  # 股票池最大股票数目
# filename=filename[1971:1972]
# filename=filename[862:863]
filename = filename[0:maxstocknum]
# 设置测试时间
back_year = 3
end = dt.datetime.now()
sta = dt.datetime.now() - dt.timedelta(days=back_year * 365)
i = 0
for fname in filename:
    df = pd.read_csv(path_root + "/datas/tdx/" + fname,
                     skiprows=[0, 1], encoding="gbk", skipfooter=1, parse_dates=[0],
                     names=['datetimes', 'open', 'high', 'low', 'close', 'volume ', 'amount'],
                     )

    # 排除新股
    if df.shape[0] < 22:
        print("此条为新股", fname, i)
        i = i + 1
        continue

    # 转换某些股票含时区，再选取时间区间，然后再判断行高。
    # print(df,df.dtypes)
    df['datetimes'] = df['datetimes'].dt.tz_localize(None)
    df = df.loc[df['datetimes'] > sta]

    # 排除新股
    if df.shape[0] < 22:
        print("此条为新股", fname, i)
        i = i + 1
        continue

    if df.iloc[0:22, 1].sum == None:
        df.iloc[0] = df.loc[df['open'] != None].ilco[0]
        print("此条开头全是空")

    data = bt.feeds.PandasData(
        # fromdate=sta,
        # todate=end,
        dataname=df,
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
    )
    cerebro.adddata(data, name=fname)

    print("注入数据", fname, i)
    i = i + 1

# 注入策略
cerebro.addstrategy(BOLLStrat)
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
cerebro.plot()
