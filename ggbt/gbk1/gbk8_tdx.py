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

# 创建策略
class SmaCross(bt.Strategy):
    # 可配置策略参数
    params = dict(
        pfast=5,  # 短期均线周期
        pslow=20,  # 长期均线周期
    )

    def log(self, txt):
        ''' Logging function for this strategy'''
        dt = self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.trade_stock={}
        sma1 = [bt.ind.SMA(d, period=self.p.pfast) for d in self.datas]
        sma2 = [bt.ind.SMA(d, period=self.p.pslow) for d in self.datas]

        self.crossover = {
            d: bt.ind.CrossOver(s1, s2)
            for d, s1, s2 in zip(self.datas, sma1, sma2)
        }

    def next(self):
        for d,self.stock_name in zip(self.datas,self.dnames):
            if not self.getposition(d).size:
                if self.crossover[d] > 0:
                    self.buy(data=d)  # 买买买
            elif self.crossover[d] < 0:
                # for name, value in vars(self.getposition(d)).items():
                #     print('%s=%s' % (name, value),"////////////////")
                # 加减仓规则，可以在next里写，也可以在sizer里写
                self.log("现在是哪个股票：%s,现有持仓：%.2f,现在价格：%.2f,现有价值：%.2f,上次开仓价格：%.2f,当前剩余资金:%.2f"
                         %(self.stock_name,self.getposition(d).size,self.getposition(d).price,
                           self.getposition(d).size*self.getposition(d).price,self.getposition(d).adjbase,self.broker.getcash()))
                self.close(data=d)  # 卖卖卖


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # broker 提交/接受了，买/卖订单则什么都不做
            return

        # 检查一个订单是否完成
        # 注意: 当资金不足时，broker会拒绝订单
        if order.status in [order.Completed]:
            # if order.isbuy():
            #     self.log(
            #         '已买入, %.2f' % order.executed.price + ' 数量, %.2f' % order.executed.size + ' 价值, %.2f' % order.executed.value + ' 手续费, %.2f' % order.executed.comm)
            #
            # elif order.issell():
            #     self.log(
            #         '已卖出, %.2f' % order.executed.price + ' 数量, %.2f' % order.executed.size + ' 价值, %.2f' % order.executed.value + ' 手续费, %.2f' % order.executed.comm)
            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            str="\nsize:%f\nvalue:%f\ncash:%f"%(order.executed.size,order.executed.value,order.executed.value)
            self.log('订单取消/保证金不足/拒绝'+str)

        # 其他状态记录为：无挂起订单
        self.order = None

    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        # if not trade.isclosed:
        #     return
        # self.log('交易利润, 毛利润 %.2f, 净利润 %.2f, 佣金 %.2f' %
        #          (trade.pnl, trade.pnlcomm, trade.commission))
        # 这是每次一个进出交易的trade触发，只记录一次买卖的盈利，估计可以建立dict存储个股的总盈亏

        # 此处报错，请注释掉，应该怎么写呢？
        # if not self.trade_stock[self.stock_name]:
        #     self.trade_stock[self.stock_name] = []
        # self.trade_stock[self.stock_name].append(trade.pnl)
        self.trade_stock[self.stock_name] = []
        self.trade_stock[self.stock_name].append(trade.pnl)
        #这样写  是最后一次盈利



    def stop(self):
        # for name, value in vars(self.broker).items():
        #     print('%s=%s' % (name, value))
        print(self.trade_stock)

cerebro = bt.Cerebro(stdstats=False)
cerebro.addobserver(bt.observers.Broker)
cerebro.addobserver(bt.observers.Trades)

time0=datetime.now()

filename = os.listdir(path_root+"/datas/tdx")
maxstocknum = 3  # 股票池最大股票数目

filename=filename[0:maxstocknum]
#设置测试时间
back_year = 3
end = dt.datetime.now()
sta = dt.datetime.now() - dt.timedelta(days=back_year * 365)
i=0
for fname in filename:
    df = pd.read_csv(path_root + "/datas/tdx/"+fname,
                     skiprows=[0, 1],  encoding="gbk",skipfooter =1,parse_dates=[0],
                     names=['datetimes', 'open', 'high', 'low', 'close', 'volume ', 'amount'],
                     )


    #排除新股
    if df.shape[0]<22:
        print("此条为新股",fname,i)
        i = i + 1
        continue

    #转换某些股票含时区，再选取时间区间，然后再判断行高。
    # print(df,df.dtypes)
    df['datetimes']=df['datetimes'].dt.tz_localize(None)
    df=df.loc[df['datetimes']>sta]

    #排除新股
    if df.shape[0]<22:
        print("此条为新股",fname,i)
        i = i + 1
        continue

    if df.iloc[0:22,1].sum==None:
        df.iloc[0]=df.loc[df['open']!=None].ilco[0]
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
        plot=False
    )
    cerebro.adddata(data,name=fname)

    print("注入数据",fname,i)
    i=i+1


# 注入策略
cerebro.addstrategy(SmaCross)
#cerebro.optstrategy(SmaCross,pfast=range(1,20,2),pslow=range(5,40,4))

# 设置现金
startcash = 10000000
cerebro.broker.setcash(startcash)
#cerebro.broker.setcommission(stampDutyCommissionScheme)
cerebro.broker.setcommission(commission=0.001)
cerebro.addsizer(LongOnly)


results = cerebro.run()
strat = results[0]


# 最终收益或亏损
pnl = (cerebro.broker.get_value() - startcash)/startcash
print('Profit ... or Loss: {:.2f}'.format(pnl))
print("用时：",datetime.now()-time0)
cerebro.addobserver(bt.observers.Broker)
cerebro.addobserver(bt.observers.Trades)
cerebro.plot()
