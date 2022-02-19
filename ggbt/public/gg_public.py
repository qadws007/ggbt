import pandas as pd


class GgPublic:

    def format_code_prefix(self, code, sep='', sh='sh', sz='sz'):

        # 如果类型是list
        if type(code) == list:
            for n, i in enumerate(code):
                if i[0:1] == '6':
                    code[n] = sh + sep + i
                else:
                    code[n] = sz + sep + i
            return code

        # 如果类型是df
        if type(code) == type(pd.DataFrame()):
            for i in code.itertuples():
                if code['code'][i[0]][0:1] == '6':
                    code['code'][i[0]] = sh + sep + code['code'][i[0]]
                else:
                    code['code'][i[0]] = sz + sep + code['code'][i[0]]
            return code

'''
import os

# 获取根目录
path_root = os.path.dirname(os.getcwd())
df = pd.read_csv(path_root + '/000300_list.csv', dtype={'品种代码': str}, encoding='utf8')
df.drop(columns=['品种名称', '纳入日期'], inplace=True)
df.columns = ['code']
df = GgPublic().format_code_prefix(df)
print(df)
'''