import pandas as pd
import datetime
import baostock as bs

lg = bs.login()


def get_datas_bs(code):
    # 设置测试时间
    back_year = 1
    sta = datetime.datetime.now() - datetime.timedelta(days=back_year * 365)
    sta = str(sta.date())
    now = str(datetime.datetime.now().date())
    print(sta, now)
    rs = bs.query_history_k_data_plus(code,
                                      'date,code,open,high,low,close,preclose,pctChg,volume,amount,turn',
                                      start_date=sta, end_date=now, frequency='d', adjustflag='2')
    print('query_history_k_data_plus respond error_code:' + rs.error_code)
    print('query_history_k_data_plus respond  error_msg:' + rs.error_msg)

    #### 打印结果集 ####
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录,将记录合并在一起
        data_list.append(rs.get_row_data())
    df = pd.DataFrame(data_list, columns=rs.fields, dtype=float)
    df['avg'] = df['amount'] / df['volume']
    #print(df)
    return df
    # self.data = pd.read_csv('test.csv')


def CalChipDistribution(df):
    # 获取一下总共交易了多少天
    rows = df.shape[0]
    # 创建一个df来存放分布
    chips = pd.DataFrame(columns={'avg': '', '比例': '', '盈亏': ''})
    # 获取发行价
    issuePrice = df['preclose'][0]
    # 把发行价添加到筹码分布里面
    # temp=pd.DataFrame(columns={'avg':issuePrice,'比例:1.0盈亏':'g'},index=['0'])
    temp = {'avg': issuePrice, '比例': 1.0, '盈亏': 'g'}
    chips = chips.append(temp, ignore_index=True)

    for i in range(0, rows):
        # 获取均价
        price = df['avg'][i]
        # 如果这个价格不在已有的筹码里面
        if price not in chips['avg'].tolist():
            # 添加到筹码分布中
            temp = {'avg': price, '比例': 0.0, '盈亏': 'g'}
            chips = chips.append(temp, ignore_index=True)
            # 其他价格的筹码比例*(1-换手率)
            chips['比例'] = chips['比例'] * (1 - df['turn'][i])
            priceIndex = chips.loc[chips['avg'] == price].index
            # 新价格的筹码比例等于换手率
            #chips['比例'][priceIndex] = df['turn'][i]
            chips.loc[priceIndex,'比例'] = df['turn'][i]
        else:
            # 所有价格的筹码比例x(1-换手率)
            chips['比例'] = chips['比例'] * (1 - df['turn'][i])
            priceIndex = chips.loc[chips['avg'] == price].index
            # 当日价格的筹码在之前变动的基础上加上换手率
            chips['比例'][priceIndex] = df['turn'][i] + chips['比例'][priceIndex]
    # 按照价格排序
    chips.sort_values('avg', inplace=True)
    currentPrice = df['avg'][rows - 1]
    # 价格高于当前价格的记为亏损
    chips.loc[chips['avg'] >= currentPrice, '盈亏'] = 'g'
    chips.loc[chips['avg'] < currentPrice,'盈亏'] = 'r'
    chips.reset_index(inplace=True, drop=True)

    chips.drop(index=chips.loc[chips['比例']<0.001].index,inplace=True)
    print(chips)
    print(chips.groupby(chips['盈亏'])['比例'].sum())
    print(chips[['avg','比例']].quantile([.1,.9]))
    return chips


if __name__ == '__main__':
    data = get_datas_bs('sh.600519')
    CalChipDistribution(data)