from datetime import datetime
import backtrader as bt
import pandas as pd
import os.path  # 管理路径
import sys
import datetime as dt
import akshare as ak
import baostock as bs
import pandas as pd
import datetime
import traceback
import get_datas_bt as gdb
from sqlalchemy import create_engine
import pandas as pd
import tushare as ts
import os
import sys

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


class SizerPercent(bt.Sizer):
    params = (
        ('percents', 10),
        ('retint', False),  # 返回整数
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        else:
            size = position.size
        if self.p.retint:
            size = int(size)

        return size


# 创建策略继承bt.Strategy
class TestStrategy(bt.Strategy):
    params = (('short', 5),
              ('long', 20),
              ('trade_msg', False),
              ('order_msg', False)
              )

    def log(self, txt, dt=None):
        # 记录策略的执行日志
        if self.p.order_msg:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 设置最小周期
        self.addminperiod(self.p.long)
        self.trade_stock = {}
        sma1 = [bt.ind.SMA(d, period=self.p.short, plot=False) for d in self.datas]
        sma2 = [bt.ind.SMA(d, period=self.p.long, plot=False) for d in self.datas]
        self.crossover = {
            d: bt.ind.CrossOver(s1, s2)
            for d, s1, s2 in zip(self.datas, sma1, sma2)
        }

    def next(self):
        for d, self.stock_name in zip(self.datas, self.dnames):
            if not self.getposition(d).size:
                if self.crossover[d] > 0:
                    self.buy(data=d)  # 买买买
            elif self.crossover[d] < 0:
                self.log("现在是哪个股票：%s,现有持仓：%.2f,现在价格：%.2f,现有价值：%.2f,上次开仓价格：%.2f,当前剩余资金:%.2f"
                         % (self.stock_name, self.getposition(d).size, self.getposition(d).price,
                            self.getposition(d).size * self.getposition(d).price, self.getposition(d).adjbase, self.broker.getcash()))
                self.close(data=d)  # 卖卖卖

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
                # print(order.executed)
            elif order.issell():
                self.log(
                    '已卖出, %.2f' % order.executed.price + ' 数量, %.2f' % order.executed.size + ' 价值, %.2f' % order.executed.value + ' 手续费, %.2f' % order.executed.comm)

            # 记录当前交易数量
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            str = "\nsize:%f\nvalue:%f\ncash:%f" % (order.executed.size, order.executed.value, order.executed.value)
            self.log('订单取消/保证金不足/拒绝' + str)

        # 其他状态记录为：无挂起订单
        self.order = None

    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        if trade.isclosed:
            dt = self.data.datetime.date()
            if self.p.trade_msg:
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


# 创建交易数据集
# cerebro = bt.Cerebro(stdstats=False)
cerebro = bt.Cerebro()
# cerebro.addobserver(bt.observers.Broker)
# cerebro.addobserver(bt.observers.Trades)
# cerebro.addobserver(bt.observers.BuySell)
cerebro.addobserver(bt.observers.DrawDown)
cerebro.addobserver(bt.observers.TimeReturn)

create_datas = gdb.GetDatasBT()
create_datas.get_datas_hs_1(cerebro, 0.5, 2)

# 加载策略
cerebro.addstrategy(TestStrategy)
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
# cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
# cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')

results = cerebro.run(tradehistory=True)
strat = results[0]
pnl = (cerebro.broker.getvalue() / startcash - 1)
pnly = pow(pnl + 1, 1 / 2)
print('收益率: %.2f' % (pnl * 100), '年化收益率：%.2f' % ((pnly - 1) * 100))
# print('夏普比率:', strat.analyzers.SharpeRatio.get_analysis())
# print('回撤指标:', strat.analyzers.DW.get_analysis())


# cerebro.plot()

from backtrader.utils.dateintern import *

plot_p_date = list(map(lambda x: num2date(x).strftime('%Y-%m-%d'), strat.array))


# exit()

def calc_border(all, nub):
    layer = 100 / (all * 2 + all + 1)
    x = nub * layer + (nub - 1) * layer * 2
    y = (all + 1 - nub) * layer + (all - nub) * layer * 2
    x = str(round(x, 2)) + '%'
    y = str(round(y, 2)) + '%'
    print(x, y)
    return x, y


from pyecharts.charts import Line, Grid,Scatter
import pyecharts.options as opts


left_border='10%'

line_1 = (
    Line()
        .add_xaxis(plot_p_date)
        .add_yaxis(
        series_name="value",
        y_axis=strat.observers.broker.l.value.array,
        label_opts=opts.LabelOpts(is_show=False),
        is_smooth=True,
        color="#FF00FF",
        xaxis_index=0, yaxis_index=0
    )
        .add_yaxis(
        series_name="cash",
        y_axis=strat.observers.broker.l.cash.array,
        label_opts=opts.LabelOpts(is_show=False),
        is_smooth=True,
        color="#0000FF",
        xaxis_index=0, yaxis_index=0
    )
        .set_global_opts(
        title_opts=opts.TitleOpts(title="账户情况", pos_top=calc_border(4, 1)[0], pos_bottom=calc_border(4, 1)[1]),
        tooltip_opts=opts.TooltipOpts(axis_pointer_type="cross"
                                      ),
        axispointer_opts=opts.AxisPointerOpts(is_show=True, link=[{"xAxisIndex": "all"}]),
        legend_opts=opts.LegendOpts(pos_left=left_border),
        datazoom_opts=[
            opts.DataZoomOpts(
                is_show=True, type_="slider", xaxis_index=[0, 0],pos_top='95%', range_start=0, range_end=100),
            opts.DataZoomOpts(
                is_show=False, type_="inside", xaxis_index=[0, 1], range_start=0, range_end=100),
            opts.DataZoomOpts(
                is_show=False, type_="inside", xaxis_index=[0, 2], range_start=0, range_end=100),
            opts.DataZoomOpts(
                is_show=False, type_="inside", xaxis_index=[0, 3], range_start=0, range_end=100),
        ],

    )
)

line_2 = (
    Line()
        .add_xaxis(plot_p_date)
        .add_yaxis(
        series_name="drawdown",
        y_axis=strat.observers.drawdown.array,
        label_opts=opts.LabelOpts(is_show=False),
        is_smooth=True,
        color="#FFF",
        xaxis_index=0, yaxis_index=1
    )

        .set_global_opts(
        title_opts=opts.TitleOpts(title="drawdown", pos_top=calc_border(4, 2)[0], pos_bottom=calc_border(4, 2)[1]),
        tooltip_opts=opts.TooltipOpts(axis_pointer_type="cross"),
        axispointer_opts=opts.AxisPointerOpts(is_show=True, link=[{"xAxisIndex": "all"}]),
        legend_opts=opts.LegendOpts(pos_left='40%')
    )
)

_scatter=(
    Scatter()
)

for i in plot_p_date:
    pass

scatter = (
    Scatter()
        .add_xaxis(plot_p_date)
        .add_yaxis("买点", plot_p_date.pricein.round(2).values.tolist()
                   , xaxis_index=0, yaxis_index=0
                   , label_opts=opts.LabelOpts(is_show=False)
                   , symbol="triangle", symbol_size=[7, 7]
                   , symbol_rotate=180
                   , itemstyle_opts=opts.ItemStyleOpts(color='#6666ff'))
        .add_yaxis("卖点", plot_p_date
                   , xaxis_index=0, yaxis_index=0
                   , label_opts=opts.LabelOpts(is_show=False)
                   , symbol="triangle", symbol_size=[9, 9],
                   itemstyle_opts=opts.ItemStyleOpts(color='#229B96'))


        .set_global_opts(
        legend_opts=opts.LegendOpts(pos_bottom="20%", pos_left="center"),
        tooltip_opts=opts.TooltipOpts(axis_pointer_type='cross')
    )

)


line_3 = (
    Line()
        .add_xaxis(plot_p_date)
        .add_yaxis(
        series_name="drawdown",
        y_axis=strat.observers.drawdown.array,
        label_opts=opts.LabelOpts(is_show=False),
        is_smooth=True,
        color="#FFF",
        xaxis_index=0, yaxis_index=2
    )

        .set_global_opts(
        title_opts=opts.TitleOpts(title="drawdown", pos_top=calc_border(4, 3)[0], pos_bottom=calc_border(4, 3)[1]),
        tooltip_opts=opts.TooltipOpts(axis_pointer_type="cross"),
        axispointer_opts=opts.AxisPointerOpts(is_show=True, link=[{"xAxisIndex": "all"}]),
        legend_opts=opts.LegendOpts(pos_left='60%')
    )
)

line_4 = (
    Line()
        .add_xaxis(plot_p_date)
        .add_yaxis(
        series_name="timereturn",
        y_axis=strat.observers.timereturn.array,
        label_opts=opts.LabelOpts(is_show=False),
        is_smooth=True,
        color="#FFF",
        xaxis_index=0, yaxis_index=3
    )
        .set_global_opts(
        title_opts=opts.TitleOpts(title="timereturn", pos_top=calc_border(4, 4)[0], pos_bottom=calc_border(4, 4)[1]),
        tooltip_opts=opts.TooltipOpts(axis_pointer_type="cross"),
        axispointer_opts=opts.AxisPointerOpts(is_show=True, link=[{"xAxisIndex": "all"}]),
        legend_opts=opts.LegendOpts(pos_left='80%'),
    )
)

grid = (
    Grid(init_opts=opts.InitOpts(width='1680px', height='850px'))
        .add(line_1, grid_opts=opts.GridOpts(1, pos_left=left_border, pos_top=calc_border(4, 1)[0], pos_bottom=calc_border(4, 1)[1]))
        .add(line_2, grid_opts=opts.GridOpts(1, pos_left=left_border, pos_top=calc_border(4, 2)[0], pos_bottom=calc_border(4, 2)[1]))
        .add(line_3, grid_opts=opts.GridOpts(1, pos_left=left_border, pos_top=calc_border(4, 3)[0], pos_bottom=calc_border(4, 3)[1]))
        .add(line_4, grid_opts=opts.GridOpts(1, pos_left=left_border, pos_top=calc_border(4, 4)[0], pos_bottom=calc_border(4, 4)[1]))

        .render("C:\\Users\\Administrator\\Desktop\\test.html")
)

os.system("C:\\Users\\Administrator\\Desktop\\test.html")
