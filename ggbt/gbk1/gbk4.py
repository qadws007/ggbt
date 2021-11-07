from datetime import datetime
import backtrader as bt
import pandas as pd
import os.path  # 管理路径
import datetime as dt
import numpy as np
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
    params = (('period_kdj', 9),
              ('period_dfast', 3),
              ('period_dslow', 3),
              )

    def __init__(self):
        self.addminperiod(int(np.max(
            [self.p.period_kdj, self.p.period_dfast, self.p.period_dslow])) + 2)
        # 保存收盘价的引用
        self.dataclose = self.datas[0].close
        # self.rsi = bt.indicators.RSI_SMA(
        #     self.data.close, period=self.p.period_rsi, upperband=self.p.short, lowerband=self.p.long)

        # self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=int(self.p.period_rsi),
        #                                                upperband=int(self.p.short), lowerband=int(self.p.long))
        self.kdj = KDJ(period_kdj=int(self.p.period_kdj), period_dfast=int(self.p.period_dfast),
                       period_dslow=int(self.p.period_dslow))
        self.kdjsignal = bt.indicators.CrossOver(self.kdj.l.J, self.kdj.l.K)

    def next(self):
        if not self.position:
            if self.kdjsignal == 1:
                self.order = self.buy()
        else:
            if  self.kdjsignal == -1:
                self.order = self.sell()


# 显示所有列
pd.set_option('display.max_columns', None)

def get_data1():
    # 创建交易数据集
    df = pd.read_csv(path_root + "/datas/47.csv", dtype='str')
    df['datetime'] = df['日期'] + " " + df['时间']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.index = df['datetime']
    df.drop(['结算价', 'datetime', '日期', '时间'], axis=1, inplace=True)
    print(df)
    return df


def get_data2(code="sh.000016",fre="D"):
    import baostock as bs
    import pandas as pd
    back_year = 10
    end = dt.datetime.now()
    sta = dt.datetime.now() - dt.timedelta(days=back_year * 365)
    #### 登陆系统 ####
    lg = bs.login()
    rs = bs.query_history_k_data_plus(code,
                                      "date,code,open,high,low,close,volume,amount,pctChg",
                                      start_date=sta.date().__str__(), end_date=end.date().__str__(), frequency=fre)
    # 打印结果集
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    result['date'] = pd.to_datetime(result['date'])
    result[['open', 'high', 'low', 'close','volume']] = result[['open', 'high', 'low', 'close','volume']].astype('float')
    #### 登出系统 ####
    bs.logout()
    df = bt.feeds.PandasData(
        # fromdate=sta,
        # todate=end,
        dataname=result,
        datetime=0,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=6,
        openinterest=-1,
    )
    print(df)
    return df




#get_data1()使用
# back_year = 2
# end = dt.datetime.now()
# sta = dt.datetime.now() - dt.timedelta(days=back_year * 30)
# data[['开盘', '最高', '最低', '收盘', '成交量']] = data[['开盘', '最高', '最低', '收盘', '成交量']].astype('float')

#get_data2()使用
data = get_data2()

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
win=0

# 评估函数，输入参数，返回评估函数值，这里是总市值，要求最大化
def runstrat(period_kdj, period_dslow, period_dfast):
    global times
    print('I am called %s ,第 %s 次.' % (datetime.now().strftime('%H:%M:%S'), times))
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy, period_kdj=period_kdj, period_dslow=period_dslow, period_dfast=period_dfast)
    cerebro.adddata(data)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer,_name='ta')
    cerebro.addsizer(bt.sizers.AllInSizer)
    #cerebro.broker.setcash(100000)  # 设置初始资金
    rs=cerebro.run()
    rs=rs[0]
    winp=rs.analyzers.ta.rets['won']['total']/(rs.analyzers.ta.rets['won']['total']+rs.analyzers.ta.rets['lost']['total'])
    times = times + 1
    # return cerebro.broker.getvalue()

    return winp


opt = optunity.maximize(runstrat, num_evals=3, solver_name='particle swarm',
                        period_kdj=[1, 40], period_dslow=[1, 30], period_dfast=[1, 30])

########################################

# 优化完成，得到最优参数结果
optimal_pars, details, _ = opt
print('Optimal Parameters:')
print('period_kdj = %.2f' % optimal_pars['period_kdj'])
print('period_dfast = %.2f' % optimal_pars['period_dfast'])
print('period_dslow = %.2f' % optimal_pars['period_dslow'])
# 利用最优参数最后回测一次，作图
cerebro = bt.Cerebro()
cerebro.addstrategy(TestStrategy,period_kdj=optimal_pars['period_kdj'],
                    period_dslow=optimal_pars['period_dslow'], period_dfast=optimal_pars['period_dfast'])
cerebro.adddata(data)
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer,_name='ta')
rs = cerebro.run()
rs = rs[0]
winp=rs.analyzers.ta.rets['won']['total']/(rs.analyzers.ta.rets['won']['total']+rs.analyzers.ta.rets['lost']['total'])
print(cerebro.broker.getvalue(),winp)
cerebro.plot()
