#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
@brief 网格交易：投资者把资金分为多份，在一价格区间内，股票下跌到（或低于）某一基准价以下一定幅度，就买入一份额度股票；上涨到（或高于）基准价以上一定幅度，
就卖出一份额度股票。每次触发后更新基准价为当前网格价格，之后不断重复上述买卖规则，从而在一系列网格中低买高卖赚取震荡行情收益。

'''
from ths_api import *


dict_params = {
    "code": "002415",
    "buy_wtjg": "dsj1",
    "buy_wtsl": "200",
    "sell_wtjg": "dsj1",
    "sell_wtsl": "200",
    "price_init": "51.9",
    "up_spread": "0.01",
    "down_spread": "0.01",
    "max_price": "120",
    "min_price": "70",
    "max_gpsl": "35000",
    "min_gpsl": "400"
}

dict_descs = {
    "code": {
        "desc": "证券代码",
        "type": "edit"
    },
    "buy_wtjg": {
        "desc": "买入价格",
        "type": "edit"
    },
    "buy_wtsl": {
        "desc": "买入数量",
        "type": "edit"
    },
    "sell_wtjg": {
        "desc": "卖出价格",
        "type": "edit"
    },
    "sell_wtsl": {
        "desc": "卖出数量",
        "type": "edit"
    },
    "price_init": {
        "desc": "初始价格",
        "type": "edit"
    },
    "up_spread": {
        "desc": "上涨价差%",
        "type": "edit"
    },
    "down_spread": {
        "desc": "下跌价差%",
        "type": "edit"
    },
    "max_price": {
        "desc": "价格上限",
        "type": "edit"
    },
    "min_price": {
        "desc": "价格下限",
        "type": "edit"
    },
    "max_gpsl": {
        "desc": "最大持仓",
        "type": "edit"
    },
    "min_gpsl": {
        "desc": "保留底仓",
        "type": "edit"
    }
}


def init():
    global dict_params
    # if context.wgjy != None:
    #    dict_params = context.wgjy
    # else:
    #    context.wgjy = dict_params
    # print('从缓存中加载dict_params', dict_params)
    context.wgjy = dict_params


def order(mmlb, code, wtjg, wtsl):
    cmdstr = '%s %s %s %s -notip' % (mmlb, code, wtjg, wtsl)
    print(cmdstr)
    xd.cmd(cmdstr)


def main():
    code = dict_params['code']

    buy_wtjg = dict_params['buy_wtjg']
    buy_wtsl = int(dict_params['buy_wtsl'])  # 每次触发后的买入委托股数

    sell_wtjg = dict_params['sell_wtjg']
    sell_wtsl = int(dict_params['sell_wtsl'])  # 每次触发后的卖出委托股数

    price_init = float(dict_params['price_init'])  # 网格交易的（初始）基准价
    up_spread = float(dict_params['up_spread'])  # 股价每上涨p_up元卖出
    down_spread = float(dict_params['down_spread'])

    # 需要增加冲高回落、触底反弹。要考虑冲高回落、触底反弹逻辑中的最高、最低价变量的持久化，确保第二天可以运行。

    max_price = float(dict_params['max_price'])  # 网格交易的价格区间上限
    min_price = float(dict_params['min_price'])  # 网格交易的价格区间下限

    max_gpsl = int(dict_params['max_gpsl'])
    min_gpsl = int(dict_params['min_gpsl'])  # 底仓的股票数量

    api = hq.ths_hq_api()
    quote = api.reg_quote(code)
    api.wait_update()

    while True:
        api.wait_update()
        price = quote[code]['price']
        # print(price)

        if price > max_price or price < min_price or (
                price > price_init * (1 + down_spread) and price < price_init * (1 - up_spread)):
            pass
        else:
            gpye = xd.g_position[code]['gpye']
            kyye = xd.g_position[code]['kyye']

            if gpye >= max_gpsl or gpye <= min_gpsl:
                pass

            if price <= price_init * (1 + down_spread) and price >= min_price:
                # order('buy', code, buy_wtjg, buy_wtsl)
                print('buy', buy_wtjg, buy_wtsl)

                price_init = price
            elif price >= price_init * (1 - up_spread) and price <= max_price:
                if sell_wtsl > kyye:
                    pass

                # order('sell', code, sell_wtjg, sell_wtsl)
                print('sell', sell_wtjg, sell_wtsl)
                price_init = price
            else:
                pass


if __name__ == '__main__':

    init()
    main()

