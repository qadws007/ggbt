import datetime
from ths_api import *
import pandas as pd
import numpy as np
import MyTT


#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为200，默认为50
pd.set_option('max_colwidth',150)
#显示数值，保留两位小数
#pd.set_option('display.float_format', lambda x: '%.2f' % x)


#例1：用get_quote获取一次某持仓股的最新分时行情数据，计算当前该股持仓市值：


code='601218'
api = hq.ths_hq_api()        #连接行情服务器
data_k=api.get_kline(code,1,240*6+1)
#print(data_k)
data_k=pd.DataFrame(data_k[code])
data_k['preclose']=data_k['close'].shift(1)
data_k['pctChg']=(data_k['close']-data_k['preclose'])/data_k['preclose']
data_k['v_pctChg']=data_k['volume']/10000/data_k['pctChg']
data_k=data_k[~data_k.isin([np.nan, np.inf, -np.inf]).any(1)]



s=data_k['v_pctChg'].quantile([0.1,0.9]).to_list()
a=data_k[['datetime','v_pctChg']]
print(a.loc[a['v_pctChg']<s[0]])
print(s)