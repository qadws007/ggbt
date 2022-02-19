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
import pymssql
from sqlalchemy import create_engine
import pandas as pd
import tushare as ts
import os
import sys
from public.gg_public import GgPublic


class GetDatasBT:

    def __init__(self):
        # 获取根目录
        self.path_root = os.path.dirname(os.getcwd())

    def use_sql(self):
        # 连接sql数据库，创建引擎
        # engine = create_engine('mssql+pymssql://sa:test@127.0.0.1/stock?charset=utf8')
        self.engine = create_engine("mysql://{}:{}@{}/{}?charset=utf8".format('root', 'root', 'localhost:3306', 'stock_datas_factor'))
        self.conn = self.engine.connect()

    def get_hs_dir(self):
        # 获取沪深300内含股目录
        directory = pd.read_csv(self.path_root + "/datas/list_000300.csv", encoding="utf8", dtype=str)
        directory = directory['品种代码'].to_list()
        return directory

    def set_datas_time(self, back_year=1):
        # 设置获取股票数据的时长
        end = dt.datetime.now()
        sta = dt.datetime.now() - dt.timedelta(days=int(back_year * 365))
        return sta, end

    def get_data_one(self, code, sta, end, engine):
        word1 = "select date,open,high,low,close,volume from `%s` where date>='%s' and date<='%s'" % (code, sta, end)
        ret1 = engine.execute(word1).fetchall()
        ret2 = pd.DataFrame(ret1, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        # print(ret2)
        return ret2

    def test1(self):
        self.use_sql()
        self.get_hs_dir()
        sta, end = self.set_datas_time(back_year=0.1)
        self.get_data_one('000001', sta, end, self.engine)

    def get_datas_hs_1(self, p_cerebro, year=1, rows=299,plot=False):
        """
        @param p_cerebro:cerbro对象
        @param year: 回测年数，从今天往前推n年
        @param rows:选取前多少个数据，从0开始
        """
        cerebro = p_cerebro
        self.use_sql()
        directory = self.get_hs_dir()[0:rows]
        directory = GgPublic().format_code_prefix(directory)
        sta, end = self.set_datas_time(back_year=year)

        for n, i in enumerate(directory):
            data0 = self.get_data_one(i, sta, end, self.engine)
            data = bt.feeds.PandasData(
                fromdate=sta,
                todate=end,
                dataname=data0,
                datetime=0,
                open=1,
                high=2,
                low=3,
                close=4,
                volume=5,
                plot=plot,
            )
            cerebro.adddata(data, name=i)
            print("加载第 %s 个数据 %s" % (n, i))
