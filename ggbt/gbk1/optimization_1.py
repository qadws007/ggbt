from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime as dt
import os.path  # 用于管理路径
import backtrader as bt  # 引入backtrader框架
import pandas as pd


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
        s1=5,  # 短1期均线周期
        s2=5,  # 短2期均线周期
        l1=10, # 长1期均线周期
        l2=10  # 长2期均线周期
    )

    def __init__(self):
        ls1 = bt.ind.SMA(period=self.p.s1)
        ls2 = bt.ind.SMA(period=self.p.s2)
        ll1 = bt.ind.SMA(period=self.p.l1)
        ll2 = bt.ind.SMA(period=self.p.l2)
        self.cross1 = bt.ind.CrossOver(ls1, ls2)  # 交叉信号
        self.cross2 = bt.ind.CrossOver(ll1, ll2)  # 交叉信号

    def next(self):
        if not self.position:  # 不在场内，则可以买入
            if self.cross1 ==1:  # 如果金叉
                self.buy()  # 买入
        elif self.cross2 == 1:  # 在场内，且死叉
            self.close()  # 卖出

    def stop(self):
        print('(s1 %3d, s2 %3d, l1 %3d, l2 %3d) Ending Value %.2f' %
              (self.p.s1, self.p.s2,self.p.l1, self.p.l2,  self.broker.getvalue()))


if __name__ == '__main__':
    back_year = 1
    end = dt.datetime.now()
    sta = dt.datetime.now() - dt.timedelta(days=back_year * 365)

    # 获取根目录
    path_root = os.path.dirname(os.getcwd())
    # 获取本脚本文件所在路径
    df = pd.read_csv(path_root + "/datas/SZ#159919.csv",encoding='gbk', dtype='str', skiprows=[0, 1], skipfooter=1,
                     names=['datetimes', 'times', 'open', 'high', 'low', 'close', 'volume', 'amount'])
    df['datetime'] = df['datetimes'] + " " + df['times']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.index = df['datetime']
    df.drop(['datetime', 'datetimes', 'times', 'amount', 'volume'], axis=1, inplace=True)
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype('float')
    print(df)
    # 创建行情数据对象，加载数据
    data = bt.feeds.PandasData(
        fromdate=sta,
        todate=end,
        dataname=df,
        open=0,
        high=1,
        low=2,
        close=3,
        volume=-1,
        openinterest=-1,
    )

    cerebro = bt.Cerebro()  # 创建cerebro
    # 在Cerebro中添加价格数据
    cerebro.adddata(data)
    # 设置启动资金

    cerebro.addsizer(LongOnly)
    comminfo = stampDutyCommissionScheme()
    cerebro.broker.addcommissioninfo(comminfo)
    startcash = 100000.0
    cerebro.broker.setcash(startcash)  # 设置初始资金
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='ta')
    # 添加策略
    strats = cerebro.optstrategy(
        SmaCross, s1=range(1, 120, 5), s2=range(2, 240, 5),l1=range(2, 240, 5), l2=range(1, 120, 5))
        #SmaCross, s1 = [5, 10, 15], s2 = [20, 30, 60], l2 = [5, 10, 15], l1 = [20, 30, 60])


    rs=cerebro.run()

    df1=pd.DataFrame()
    for i in rs:
        try:
            pnl =i[0].analyzers.ta.rets['pnl']['net']['total']/startcash
            pnly = pow(pnl + 1, 1 / back_year)-1
            times = i[0].analyzers.ta.rets['long']['total']
            pwon = i[0].analyzers.ta.rets['long']['won'] / times
        except:
            pnly=0
            times=0
            pwon = 0
            #print('error')
        s1=i[0].params.s1
        s2 = i[0].params.s2
        l1 = i[0].params.l1
        l2 = i[0].params.l2
        if 0 > pnly or times < 100 * back_year or pwon < 0.44:
            continue
        ret= pd.DataFrame([[s1, s2, l1, l2, times, pwon, pnly]], columns=['s1', 's2', 'l1', 'l2', 'times', 'pwon', 'pnly'])
        df1=df1.append(ret,ignore_index=True)
    print(df1)
    df1.to_csv(r'C:\Users\Administrator\Desktop\gg.csv')

