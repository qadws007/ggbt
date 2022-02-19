# -*- coding: utf-8 -*-
"""
Created on Sun Aug  1 09:39:12 2021

@author: Brandon
"""

# 'sh.000016'上证50，'sh.000905'中证500，'sh.000300'沪深300
start_date_str = '2020-01-01'
end_date_str = "2021-12-31"
start_value = 10000 * 150
fast = 5
slow = 20
import numpy as np
import pandas as pd
import backtrader as bt
import pymysql
import os
import datetime
import matplotlib.pyplot as plt
from pyecharts.charts import Kline, Line, Bar, Grid, Scatter
from pyecharts import options as opts
# import matplotlib as plt
from datetime import datetime, timedelta
from public.gg_public import GgPublic

# 获取根目录
path_root = os.path.dirname(os.getcwd())
directory = pd.read_csv(path_root + "/datas/list_000300.csv", encoding="utf8", dtype=str)
directory = directory['品种代码'].to_list()
directory = GgPublic().format_code_prefix(directory)
codes = directory

# codes = ['sh000016']

pd.set_option('display.max_columns', None)
n = timedelta(days=15)


class MyStrategy(bt.Strategy):
    params = (
        ('fast_period', fast),
        ('slow_period', slow),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        print(f"----------------------------{self.data._name}------------------------------")
        print(f'{self.datas[0].lines.getlinealiases()}')
        # print(f'{self.datas[0].lines.amount[0]}')
        self.bar_executed = 0
        self.count = 0
        self.my_buy_dict = {}
        self.last_month = None
        self.dataclose = self.datas[0].close
        self.dataearlyclose = self.datas[0].close(-1)  # 前一天的收盘价
        self.chg = (self.dataclose - self.dataearlyclose) / self.dataearlyclose
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period)
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period)
        # print(self.slow_sma.data0_amount)
        self.fast_amount = bt.indicators.SimpleMovingAverage(
            self.datas[0].amount, period=self.params.fast_period)
        self.slow_amount = bt.indicators.SimpleMovingAverage(
            self.datas[0].amount, period=self.params.slow_period)

    def start(self):
        self.mystats0, self.buytrade, self.selltrade = [], [], []

    def prenext(self):
        pass

    def notify_trade(self, trade):
        # 检查交易trade是关闭
        if not trade.isclosed:
            return
        self.log('交易利润OPERATION PROFIT, 毛利GROSS {:.2f}, 净利NET{:.2f},资产{:.2f},现金{:.2f}'.format(trade.pnl, trade.pnlcomm, self.broker.get_value(), self.broker.get_cash()))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 检查订单执行状态order.status：
            # Buy/Sell order submitted/accepted to/by broker
            # broker经纪人：submitted提交/accepted接受,Buy买单/Sell卖单
            # 正常流程，无需额外操作
            return
        # 检查订单order是否完成
        # 注意: 如果现金不足，经纪人broker会拒绝订单reject order
        # 可以修改相关参数，调整进行空头交易
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"第{self.count}次加仓")
                self.log('买单执行BUY EXECUTED, 报价{:.2f},交易量{},成交额{:.2f},剩余现金{:.2f},股票市值{:.2f},佣金{:.2f},持仓成本{:.2f}' \
                         .format(order.executed.price,
                                 order.executed.size,
                                 order.executed.value,
                                 self.broker.get_cash(),
                                 self.broker.getvalue(datas=[self.datas[0]]),
                                 order.executed.comm,
                                 self.getposition().price))
                self.buytrade.append([self.datas[0].datetime.date(0), order.executed.price])
                self.bar_executed = len(self)
            elif order.issell():
                self.log('卖单执行SELL EXECUTED,报价：{:.2f},成交量{},成交额{:.2f},佣金{:.2f}'.format(order.executed.price, order.executed.size, order.executed.size * order.executed.price, order.executed.comm))
                self.selltrade.append([self.datas[0].datetime.date(0), order.executed.price])
                # self.bar_executed = len(self)
            # self.log(f"售卖次数{self.bar_executed})
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单Order： 取消Canceled/保证金Margin/拒绝Rejected')
        # 检查完成，没有交易中订单（pending order）
        self.order = None

    def next(self):
        total_value = self.broker.get_value()
        total_cash = self.broker.get_cash()
        # 现在持仓的股票数目
        total_holding_stock_num = self.getposition().size  # 仓位
        total_holding_stock_price = self.getposition().price  # 持仓成本股价
        cost = total_holding_stock_num * total_holding_stock_price  # 持仓成本
        # adjbase_price=self.getposition().adjbase
        # 得到当天的时间
        current_date = self.datas[0].datetime.date(0)
        if (self.chg < -0.020
                # and  self.fast_sma[0]<self.slow_sma[0] # 下降趋势加仓
                # and (self.slow_sma[0]-self.slow_sma[-5])/self.slow_sma[-5]<0.015
                # and self.count<48 # 限制加仓次数
                and len(self) >= (self.bar_executed + 5)):
            self.price = self.datas[0].close[0]
            size = int(15000 * abs(self.chg * 100) / (self.price))
            self.order = self.buy(data, exectype=bt.Order.Market, size=size)
            self.count += 1
        # self.log('Close{} 资产：{:.2f},现金{:.2f},成本:{:.2f},成本股价{:.2f}'.format(self.dataclose[0],self.broker.getvalue(),total_cash,cost,total_holding_stock_price))
        if self.position:
            if (total_value - total_cash - cost) / cost >= 0.10:
                self.count = 0
                self.order = self.close()
                self.log('清仓SELL CREATE, {:.2f},成本股价{:.2f},最大回撤{:.2%}'.format(self.dataclose[0], self.getposition().price, self.stats.drawdown.maxdrawdown[0]))
            elif (total_value - total_cash - cost) / cost >= 0.10:
                # 执行卖出
                size = int(15000 * abs(self.chg * 100) / (self.price) * (self.count / 5))
                if self.chg >= 0.02 and total_holding_stock_num >= size:
                    self.log('SELL CREATE, {:.2f},成本股价{:.2f},最大回撤{:.2%}'.format(self.dataclose[0], self.getposition().price, self.stats.drawdown.maxdrawdown[0]))
                    self.order = self.sell(size=(size))
                    self.price = self.datas[0].close[0]
                    self.log(f'SellPrice:{self.price}')
                elif self.chg >= 0.02 and total_holding_stock_num < size:
                    self.count = 0
                    # self.order=self.close()
                    self.order_target_percent(data=self.datas[0], target=0.0)
                    self.log('清仓SELL CREATE, {:.2f},成本股价{:.2f},最大回撤{:.2%}'.format(self.dataclose[0], self.getposition().price, self.stats.drawdown.maxdrawdown[0]))
        ss = [self.data.datetime.date(-1).strftime('%Y-%m-%d'),
              '%.4f' % self.stats.buysell.data_open[-1],
              '%.4f' % self.stats.buysell.data_close[-1],
              '%.4f' % self.stats.buysell.data_low[-1],
              '%.4f' % self.stats.buysell.data_high[-1],
              '%.4f' % self.stats.drawdown.drawdown[0],
              '%.4f' % self.stats.drawdown.maxdrawdown[0],
              '%.4f' % self.stats.timereturn.line[0],
              '%.4f' % self.stats.broker.value[0],
              '%.4f' % self.stats.broker.cash[0],
              '%.4f' % self.getposition().price
              ]
        self.mystats0.append(ss)

    def stop(self):
        '''
            当运行到最后一根 bar 后， next 中记录的是上一根 bar 的收益
            stop 是在 next 运行完后才运行的，此时 observers 已经计算完 最后一根 bar 的收益了
            所以可以在 stop 中获取最后一根 bar 的收益
        '''
        self.mystats0.append([self.data.datetime.date(0).strftime('%Y-%m-%d'),
                              '%.4f' % self.stats.buysell.data_open[0],
                              '%.4f' % self.stats.buysell.data_close[0],
                              '%.4f' % self.stats.buysell.data_low[0],
                              '%.4f' % self.stats.buysell.data_high[0],
                              '%.4f' % self.stats.drawdown.drawdown[0],
                              '%.4f' % self.stats.drawdown.maxdrawdown[0],
                              '%.4f' % self.stats.timereturn.line[0],
                              '%.4f' % self.stats.broker.value[0],
                              '%.4f' % self.stats.broker.cash[0],
                              '%.4f' % self.getposition().price
                              ])
        self.mystats = pd.DataFrame(data=self.mystats0, columns=['date',
                                                                 'open',
                                                                 'close',
                                                                 'low',
                                                                 'high',
                                                                 'drawdown',
                                                                 'maxdrawdown',
                                                                 'timereturn',
                                                                 'value',
                                                                 'cash',
                                                                 'costprice'
                                                                 ])
        self.buytrade = pd.DataFrame(data=self.buytrade, columns=['datein', 'pricein'])
        # self.buytrade.to_csv("E:\\Brandon\\Desktop\\buytrade.csv", encoding="gbk", index=False)
        self.selltrade = pd.DataFrame(data=self.selltrade, columns=['dateout', 'priceout'])
        # self.selltrade.to_csv("E:\\Brandon\\Desktop\\selltrade.csv", encoding="gbk", index=False)
        self.mystats = self.mystats[1:len(self.mystats) + 1]


# %%PandasDate_more amount
class PandasData_more(bt.feeds.PandasData):
    lines = ('amount',)  # 要添加的线
    # 设置 line 在数据源上的列位置
    params = (
        ('amount', -1),
    )


class stampDutyCommissionScheme(bt.CommInfoBase):
    params = (
        ('stamp_duty', 0.005),  # 印花税率
        ('percabs', True),
    )

    def _gotcommission(self, size, price, pseudoexec):
        if size > 0:  # 买入，不考虑印花税
            return size * price * self.p.commission
        elif size < 0:  # 卖出，考虑印花税
            return -size * price * (self.p.stamp_duty + self.p.commission)
        else:
            return 0


# %%Class交易记录
class trade_list(bt.Analyzer):
    # 自定义分析器，调用时，需要设置 cerebro.run(tradehistory=True)
    def __init__(self):
        self.trades = []
        self.cumprofit = 0.0

    def notify_trade(self, trade):
        if trade.isclosed:
            brokervalue = self.strategy.broker.getvalue()
            dir = 'short'
            if trade.history[0].event.size > 0: dir = 'long'
            pricein = trade.history[len(trade.history) - 1].status.price
            priceout = trade.history[len(trade.history) - 1].event.price
            datein = bt.num2date(trade.history[0].status.dt)
            dateout = bt.num2date(trade.history[len(trade.history) - 1].status.dt)
            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()
            pcntchange = 100 * priceout / pricein - 100
            pnl = trade.history[len(trade.history) - 1].status.pnlcomm
            pnlpcnt = 100 * pnl / brokervalue
            barlen = trade.history[len(trade.history) - 1].status.barlen
            pbar = pnl / barlen
            self.cumprofit += pnl
            size = value = 0.0
            for record in trade.history:
                if abs(size) < abs(record.status.size):
                    size = record.status.size
                    value = record.status.value
            highest_in_trade = max(trade.data.high.get(ago=0, size=barlen + 1))
            lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen + 1))
            hp = 100 * (highest_in_trade - pricein) / pricein
            lp = 100 * (lowest_in_trade - pricein) / pricein
            if dir == 'long':
                mfe = hp
                mae = lp
            if dir == 'short':
                mfe = -lp
                mae = -hp
            self.trades.append({'ref': trade.ref,
                                'ticker': trade.data._name,
                                'dir': dir,
                                'datein': datein,
                                'pricein': pricein,
                                'dateout': dateout,
                                'priceout': priceout,
                                'chng%': round(pcntchange, 2),
                                'pnl': pnl, 'pnl%': round(pnlpcnt, 2),
                                'size': size,
                                'value': value,
                                'cumpnl': self.cumprofit,
                                'nbars': barlen, 'pnl/bar': round(pbar, 2),
                                'mfe%': round(mfe, 2), 'mae%': round(mae, 2)})

    def get_analysis(self):
        return self.trades


# %%BackTrader主程序

# 以股票002537为例
# start_date=datetime.datetime.strptime(start_date_str,"%Y%m%d")
# end_date=datetime.datetime.strptime(end_date_str,"%Y%m%d")
def get_datas(code, start_date_str, end_date_str):
    connect = pymysql.connect(host='localhost', user='root', database='stock_datas_factor', password='root', port=3306, charset='utf8mb4')
    sql = f"SELECT `date`,`open`,`high`,`low`,`close`,`volume` FROM `{code}` where `date` between '{start_date_str}' and '{end_date_str}';"  # 获取数据库中最近的原有个股数据
    # print(sql)
    df = pd.read_sql(sql, connect)
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(lambda x: pd.to_numeric(x))
    # df.index=pd.to_datetime(df.date)
    df.date = pd.to_datetime(df.date)

    # df.code=df.code.str.split(".",expand=True)[1]
    # df['openinterest'] = 0
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    return df


for code in codes:
    df = get_datas(code, start_date_str, end_date_str)
    start_date = min(df.date)
    end_date = max(df.date)
    if not 'pctChg' in df.columns:
        df['price_change'] = df['close'].diff()
    ups = df.where(df.price_change > 0, 0)['volume']
    downs = df.where(~(df.price_change > 0), 0)['volume']
    ups_amount = df.where(df.price_change > 0, 0)['volume']
    downs_amount = df.where(~(df.price_change > 0), 0)['volume']
    monthdelta = np.ceil((end_date - start_date).days / 30)
    # 加载数据，回测期间
    data = PandasData_more(dataname=df,
                           datetime=0,
                           open=1,
                           high=2,
                           low=3,
                           close=4,
                           volume=5,
                           fromdate=start_date,
                           todate=end_date)
    # data = bt.feeds.PandasData(dataname=datafeed1 )
    # 初始化cerebro回测系统设置
    cerebro = bt.Cerebro()
    # 加载数据
    cerebro.adddata(data, name=code)
    # 将交易策略加载到回测系统中
    cerebro.addstrategy(MyStrategy)
    # 设置初始资本为100,000
    # start_value=150000*monthdelta
    cerebro.broker.setcash(start_value)
    # #每次固定交易数量
    # cerebro.addsizer(bt.sizers.FixedSize, stake=200000)
    # 手续费
    # comminfo = stampDutyCommissionScheme(stamp_duty=0.005,commission=0.001)
    # cerebro.broker.addcommissioninfo(comminfo)
    cerebro.broker.setcommission(commission=0.0025)
    # 滑点：双边各 0.0001
    cerebro.broker.set_slippage_perc(perc=0.0001)
    print('初始资金: %.2f' % cerebro.broker.getvalue())
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='Returns')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='SQN')
    # cerebro.addanalyzer(trade_list, _name='tradelist')
    # 添加观测器observers
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addobserver(bt.observers.TimeReturn)
    # 防止下单时现金不够被拒绝。只在执行时检查现金够不够。
    cerebro.broker.set_checksubmit(False)
    # cerebro.addwriter(bt.WriterFile, csv=True,out='E:\\Brandon\\Desktop\\mywriter.csv',rounding=2)
    # 运行回测系统
    results = cerebro.run(tradehistory=True)
    strat = results[0]
    end_value = cerebro.broker.getvalue()
    # 返回日度收益率序列
    # daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
    DrawDown = pd.Series(dict(strat.analyzers.DW.get_analysis()))
    print("收益:{}%".format(round((end_value - start_value) / start_value * 100, 4)))
    print("年化收益率:\n{}".format(pd.Series(dict(strat.analyzers.AnnualReturn.get_analysis())).apply(lambda x: str(round(x * 100, 4)) + '%')))
    print('夏普比率:', strat.analyzers.SharpeRatio.get_analysis())
    print('回撤指标:', strat.analyzers.DW.get_analysis())
    print('投入本金:{:,.2f}'.format(cerebro.broker.startingcash))
    print('现金:{:,.2f}'.format(cerebro.broker.getcash()))
    print('股票市值:{:,.2f}'.format(cerebro.broker.getvalue(datas=[data])))
    print('最终资金:{:,.2f}'.format(end_value))
    print('收益:{:,.2f}'.format(end_value - start_value))
    # print("投资回报率:{:.2%}".format(strat.analyzers.Returns.get_analysis()['rtot']))
    # SNQ 1.6~1.9凑合用，2.0~2.4普通，2.5~2.9好，3.0~5.0杰出，5.1~6.0一流，7.0以上极好，SNQ=（平均获利/标准差）*年交易次数的平方根
    print("SQN:{}".format(strat.analyzers.SQN.get_analysis()))
    connect = pymysql.connect(host='localhost', user='root', database='stock_datas_factor', password='root', port=3306, charset='utf8mb4')
    # sql=f"SELECT `code` ,`code_name` as name FROM baostock_basic where `code`='{code}';"  #获取数据库中最近的原有个股数据
    # code_name=pd.read_sql(sql,connect)
    code_name = pd.DataFrame({'code': ['123456'], 'name': [code]})
    print(code_name.name[0])
    # plt.figure()
    cerebro.plot()
    # print(ret)
    from backtrader_plotting import Bokeh
    from backtrader_plotting.schemes import Tradimo
    from bokeh.io import show, save, output_file

    # b=Bokeh(style='bar') #黑底
    # b=Bokeh(style='bar',tabs='multi') #黑底，多页
    # b=Bokeh(style='bar',scheme=Tradimo()) # 传统白底，单页
    # b=Bokeh(style='bar',tabs='multi',scheme=Tradimo()) #传统白底，多页
    # cerebro.plot(b)
    # 曲线绘图输出
    # cerebro.plot(style='bar')
    # cerebro.plot(style='candlestick')
    # cerebro.plot()
    # b=Bokeh(style='bar') #黑底
    # b=Bokeh_1(style='bar',tabs='multi') #黑底，多页
    fnames = "E:/Brandon/Desktop/bt_bokeh_plot.html"
    # f = open("E:/Brandon/Desktop/bt_bokeh_plot.html","w")
    b = Bokeh(style='bar', tabs='multi', filename=fnames, output_mode='show')  # 黑底，多页
    # b=Bokeh(style='bar',scheme=Tradimo()) # 传统白底，单页
    # b=Bokeh(style='bar',tabs='multi',scheme=Tradimo()) #传统白底，多页
    output_file(fnames, mode='cdn', title='超买超卖')
    cerebro.plot(b)
    plt.show()
    # %%画图数据处理
    cerebro.addanalyzer(trade_list, _name='tradelist')
    results = cerebro.run(tradehistory=True)
    ret = pd.DataFrame(results[0].analyzers.tradelist.get_analysis())
    # ret.to_csv("E:\\Brandon\\Desktop\\ret.csv", encoding="gbk", index=False)
    mystats = pd.DataFrame(results[0].mystats)
    buytrade = pd.DataFrame(results[0].buytrade)
    selltrade = pd.DataFrame(results[0].selltrade)
    mystats.date = pd.to_datetime(mystats.date).dt.date
    buytrade.datein = pd.to_datetime(buytrade.datein).dt.date
    selltrade.dateout = pd.to_datetime(selltrade.dateout).dt.date
    # mystats.to_csv("E:\\Brandon\\Desktop\\mystats.csv", encoding="gbk", index=False)
    df_plot0 = pd.merge(left=mystats, right=buytrade, how='left', left_on=mystats['date'], right_on=buytrade['datein'])
    df_plot0.drop(columns=['key_0'], inplace=True)
    df_plot1 = pd.merge(left=df_plot0, right=selltrade, how='left', left_on=df_plot0['date'], right_on=selltrade['dateout'])
    df_plot1.drop(columns=['key_0'], inplace=True)
    try:
        df_plot = pd.merge(left=df_plot1, right=ret[['dateout', 'cumpnl']], how='left', left_on=df_plot1['dateout'], right_on=ret['dateout'])
        df_plot.drop(columns=['key_0'], inplace=True)
        df_plot.cumpnl.fillna(method='ffill', inplace=True)
        priceouta = df_plot.priceout.round(2).values.tolist()
        cumpnla = df_plot.cumpnl.values.tolist()
    except KeyError:
        print("NO SELL！！！")
        df_plot = df_plot1.copy()
        priceouta = df_plot.priceout.copy()
        priceouta[len(df_plot) - 1] = float(df_plot.close[len(df_plot) - 1])
        cumpnla = [0]
    df_plot.date = df_plot.date.apply(lambda x: x.strftime('%Y-%m-%d'))
    df_plot[['open', 'high', 'low', 'close', 'costprice']] = df_plot[['open', 'high', 'low', 'close', 'costprice']].apply(lambda x: pd.to_numeric(x))
    df_plot['costprice'] = df_plot['costprice'].mask(df_plot['costprice'] <= 0, None)

    # df_plot.to_csv("E:\\Brandon\\Desktop\\df_plot.csv", encoding="gbk", index=False)
    # %%画图
    # cerebro.plot()
    # plt.show()
    kline = (
        Line()
            .add_xaxis(df_plot.date.values.tolist())
            .add_yaxis("{}".format(code), df_plot[['open', 'close', 'low', 'high']].close.values.tolist()
                       , itemstyle_opts=opts.ItemStyleOpts(color='#DF0000')
                       , xaxis_index=0, yaxis_index=0
                       , markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="最大值", symbol='pin', symbol_size=[20, 20]),
                    opts.MarkPointItem(type_="min", name="最小值", symbol='arrow', symbol_size=[10, 20]),
                ],
                label_opts=opts.LabelOpts(position="inside", color="#339", font_weight='bold')  ##标签字体颜色
            ),
                       label_opts=opts.LabelOpts(is_show=False),  # 隐藏主数据标签
                       )
            .set_global_opts(
            legend_opts=opts.LegendOpts(pos_top="2%"),
            xaxis_opts=opts.AxisOpts(is_scale=True),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False, type_="inside", xaxis_index=[0, 0], range_start=0, range_end=100),
                opts.DataZoomOpts(
                    is_show=True, type_="slider", xaxis_index=[0, 1], pos_top="95%", range_start=0, range_end=100),
                opts.DataZoomOpts(
                    is_show=False, type_="inside", xaxis_index=[0, 1], range_start=0, range_end=100),
                opts.DataZoomOpts(
                    is_show=False, type_="inside", xaxis_index=[0, 2], range_start=0, range_end=100),
                opts.DataZoomOpts(
                    is_show=False, type_="inside", xaxis_index=[0, 3], range_start=0, range_end=100),
                opts.DataZoomOpts(
                    is_show=False, type_="inside", xaxis_index=[0, 4], range_start=0, range_end=100),
                # opts.DataZoomOpts(
                #     is_show=False,type_="inside", xaxis_index=[0, 4],  range_start=0,range_end=100),
            ],
            # 三个图的 axis 连在一块
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
            title_opts=opts.TitleOpts(title="{}K线图".format(code_name.name[0])),
            tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
        )  # 全局配置
        # .render("E:\\Brandon\\Desktop\\kline.html")
    )
    kline_line = (
        Line()
            .add_xaxis(df_plot.date.values.tolist())
            # .add_yaxis(f"{fast}天均线", df_plot.close.rolling(window=fast,min_periods=fast).mean().values.tolist()
            #             ,xaxis_index=0, yaxis_index=0)
            .add_yaxis(f"{slow}天均线", df_plot.close.rolling(window=slow, min_periods=slow).mean().values.tolist()
                       , itemstyle_opts=opts.ItemStyleOpts(color='#EEAA00')
                       , xaxis_index=0, yaxis_index=0)
            # .add_yaxis("180天均线", df_plot.close.rolling(window=180,min_periods=180).mean().values.tolist()
            #     ,xaxis_index=0, yaxis_index=0)
            .add_yaxis("成本价", df_plot.costprice.values.tolist(), itemstyle_opts=opts.ItemStyleOpts(color='#000000')
                       , xaxis_index=0, yaxis_index=0)
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        # .set_global_opts(title_opts=opts.TitleOpts(title="Grid-Bar"))
    )
    scatter = (
        Scatter()
            .add_xaxis(df_plot.date.values.tolist())
            .add_yaxis("买点", df_plot.pricein.round(2).values.tolist()
                       , xaxis_index=0, yaxis_index=0
                       , label_opts=opts.LabelOpts(is_show=False)
                       , symbol="triangle", symbol_size=[7, 7]
                       , symbol_rotate=180
                       , itemstyle_opts=opts.ItemStyleOpts(color='#6666ff'))
            .add_yaxis("卖点", priceouta
                       , xaxis_index=0, yaxis_index=0
                       , label_opts=opts.LabelOpts(is_show=False)
                       , symbol="triangle", symbol_size=[9, 9],
                       itemstyle_opts=opts.ItemStyleOpts(color='#229B96'))
            # .set_series_opts(label_opts=opts.LabelOpts(is_show=True),)
            .set_global_opts(
            # title_opts=opts.TitleOpts(title="交易量", subtitle="元"),
            legend_opts=opts.LegendOpts(pos_bottom="20%", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
        )
    )
    bar1 = (
        Bar()
            .add_xaxis(df_plot.date.values.tolist())
            .add_yaxis("", ups.values.tolist(), xaxis_index=0, yaxis_index=1, gap='-100%', itemstyle_opts=opts.ItemStyleOpts(color='#A33B33'))
            .add_yaxis("", downs.values.tolist(), xaxis_index=0, yaxis_index=1, gap='-100%', itemstyle_opts=opts.ItemStyleOpts(color='#3C4856'))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(yaxis_opts=opts.AxisOpts(name="交易量", split_number=3, name_gap=5))
            # .set_global_opts(title_opts=opts.TitleOpts(title="Grid-Bar"))
            .set_global_opts(
            # title_opts=opts.TitleOpts(title="交易量", subtitle="元"),
            legend_opts=opts.LegendOpts(pos_bottom="65%", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
        )
    )
    volume_line = (
        Line()
            .add_xaxis(df_plot.date.values.tolist())
            .add_yaxis("20日均线", df.volume.rolling(window=20, min_periods=20).mean().round(decimals=2).values.tolist()
                       , xaxis_index=0, yaxis_index=1
                       , label_opts=opts.LabelOpts(is_show=False))
            .add_yaxis("60日均线", df.volume.rolling(window=60, min_periods=60).mean().round(decimals=2).values.tolist()
                       , xaxis_index=0, yaxis_index=1
                       , label_opts=opts.LabelOpts(is_show=False))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False), )
            .set_global_opts(
            # title_opts=opts.TitleOpts(title="交易量", subtitle="元"),
            legend_opts=opts.LegendOpts(pos_bottom="65%", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
        )
    )
    line_value = (
        Line()
            .add_xaxis(df_plot.date.values.tolist())
            .add_yaxis("资产", df_plot.value.values.tolist(), xaxis_index=0, yaxis_index=2, itemstyle_opts=opts.ItemStyleOpts(color='#A33B33'))
            .add_yaxis("现金", df_plot.cash.values.tolist(), xaxis_index=0, yaxis_index=2, itemstyle_opts=opts.ItemStyleOpts(color='#3C4856'))
            .add_yaxis("累计利润", cumpnla, xaxis_index=0, yaxis_index=2, itemstyle_opts=opts.ItemStyleOpts(color='#3Ca856'))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(yaxis_opts=opts.AxisOpts(name="资产与现金", split_number=3, name_gap=5))
            # .set_global_opts(title_opts=opts.TitleOpts(title="Grid-Bar"))
            .set_global_opts(
            # title_opts=opts.TitleOpts(title="交易量", subtitle="元"),
            legend_opts=opts.LegendOpts(pos_bottom="50%", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
        )
    )
    line_drawdown = (
        Line()
            .add_xaxis(df_plot.date.values.tolist())
            .add_yaxis("DrawDown", df_plot.drawdown.values.tolist(), xaxis_index=0, yaxis_index=3, itemstyle_opts=opts.ItemStyleOpts(color='#A33B33'))
            .add_yaxis("MaxDrawDown", df_plot.maxdrawdown.values.tolist(), xaxis_index=0, yaxis_index=3, itemstyle_opts=opts.ItemStyleOpts(color='#3C4856'))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(yaxis_opts=opts.AxisOpts(name="Return", split_number=3, name_gap=5))
            # .set_global_opts(title_opts=opts.TitleOpts(title="Grid-Bar"))
            .set_global_opts(
            # title_opts=opts.TitleOpts(title="交易量", subtitle="元"),
            legend_opts=opts.LegendOpts(pos_bottom="35%", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
        )
    )
    line_return = (
        Line()
            .add_xaxis(df_plot.date.values.tolist())
            .add_yaxis("TimeReturn", df_plot.timereturn.values.tolist(), xaxis_index=0, yaxis_index=4, itemstyle_opts=opts.ItemStyleOpts(color='#A33B33'))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(yaxis_opts=opts.AxisOpts(name="TimeReturn", split_number=3, name_gap=5))
            # .set_global_opts(title_opts=opts.TitleOpts(title="Grid-Bar"))
            .set_global_opts(
            # title_opts=opts.TitleOpts(title="交易量", subtitle="元"),
            legend_opts=opts.LegendOpts(pos_bottom="20%", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
        )
    )
    overlap_scatter = kline.overlap(scatter)
    overlap_kline = overlap_scatter.overlap(kline_line)
    overlap_volume_line = bar1.overlap(volume_line)
    # overlap_volume_line =overlap_kline.overlap(bar1)
    # overlap_volume_line_bar =overlap_volume_line.overlap(volume_line)
    grid = (
        Grid()
            .add(overlap_kline, grid_opts=opts.GridOpts(pos_top='8%', pos_bottom="75%", pos_left='15%', pos_right='5%'))
            .add(overlap_volume_line, grid_opts=opts.GridOpts(pos_top='32%', pos_bottom="60%", pos_left='15%', pos_right='5%'))
            .add(line_value, grid_opts=opts.GridOpts(pos_top='47%', pos_bottom="45%", pos_left='15%', pos_right='5%'))
            .add(line_drawdown, grid_opts=opts.GridOpts(pos_top='63%', pos_bottom="30%", pos_left='15%', pos_right='5%'))
            .add(line_return, grid_opts=opts.GridOpts(pos_top='80%', pos_bottom="10%", pos_left='15%', pos_right='5%'))
    )
    grid.render("C:\\Users\\Administrator\\Desktop\\{}超买卖走势线图-{}-{}.html".format(code_name.name[0], start_date_str, end_date_str))
