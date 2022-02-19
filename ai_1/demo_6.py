import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.datasets import load_boston
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, SGDRegressor, Ridge, RidgeCV,SGDOneClassSVM,LogisticRegression
from sklearn.metrics import mean_squared_error
from sklearn import tree,ensemble,svm
from sklearn.neighbors import KNeighborsRegressor
import warnings
warnings.filterwarnings("ignore")
# 获取根目录
path_root = os.path.abspath(os.path.dirname(os.getcwd()))

#获取数据--------------------------
import baostock as bs
import pandas as pd

pd.set_option('display.max_columns', None) #显示完整的列
#pd.set_option('display.max_rows', None) #显示完整的行
np.set_printoptions(formatter={'all':lambda x: '%.2f' % x})
pd.set_option('display.float_format',lambda x : '%.2f' % x)

def log_write(text):
    with open("log.txt", "a",encoding='utf8') as f:
        f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" "+text+'\n')  # 自带文件关闭功能，不需要再写f.close()

log_write('开始执行运算')
#### 登陆系统 ####
lg = bs.login()

#### 获取沪深A股历史K线数据 ####
# 详细指标参数，参见“历史行情指标参数”章节；“分钟线”参数与“日线”参数不同。“分钟线”不包含指数。
# 分钟线指标：date,time,code,open,high,low,close,volume,amount,adjustflag
# 周月线指标：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg
rs = bs.query_history_k_data_plus("sh.000300",
    "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
    start_date='2005-01-01',
    frequency="d", adjustflag="2")


#### 打印结果集 ####
data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
df = pd.DataFrame(data_list, columns=rs.fields)

#### 结果集输出到csv文件 ####
#result.to_csv("D:\\history_A_stock_k_data.csv", index=False)


#### 登出系统 ####
bs.logout()
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
df=df.astype(float)

#获取数据--------------------------


# 获取本脚本文件所在路径
# df = pd.read_csv(r'C:\Users\Administrator\Desktop/SZ#159919.csv', encoding='gbk', skiprows=[0, 1], skipfooter=1, parse_dates=[0],
#                  names=['datetimes', 'open', 'high', 'low', 'close', 'volume', 'amount'], index_col="datetimes")
df1 = df['close'].copy()
t = 2
s1 = []
log_write('循环次数为：%s'%t)
for i in range(t):
    # 2.数据集划分
    x = df.shift(1)[1:]
    y = df1[1:]

    # 3.特征工程-标准化
    transfer = StandardScaler()
    x_train = transfer.fit_transform(x)


    # 4.机器学习-线性回归(特征方程)
    #estimator = SGDRegressor(max_iter=10 ^ 12, learning_rate='adaptive', eta0=0.001)
    estimator = ensemble.RandomForestClassifier()

    #训练

    estimator.fit(x_train, y.astype(int).astype(float))
    #y_train.astype(int).astype(float)
    # 5.模型评估
    # 5.1 获取系数等值
    x1=transfer.fit_transform(df)
    y_predict = estimator.predict(x1)
    s1.append([y_predict[-11:]])
    print(i,'次',y_predict[-11:])


a=np.mean(s1,axis=0)
b=pd.DataFrame(a[0])
b.columns=['预测']
b['实际']=pd.DataFrame(df1[-10:].values)
plt.rcParams['font.sans-serif'] = ['SimHei']
ax =b.plot(marker='o',use_index=False)
ax.set_title('沪深300预测 '+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
fig = ax.get_figure()

for i in b.index :
    plt.text(i, b['预测'][i], '%.3f' % b['预测'][i], ha='center')
    plt.text(i, b['实际'][i], '%.3f' % b['实际'][i], ha='center')
fig.savefig('fig.png')
plt.show()
plt.close()
log_write('代码执行完毕，准备关机/结束进程')

#os.system('shutdown /s /t 60')

