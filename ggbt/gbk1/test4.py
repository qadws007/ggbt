import pandas as pd
import numpy as np


list1 =pd.read_csv(r'C:\Users\Administrator\Desktop\gg1.csv')

x=list1[(list1['pnly']>1.1) & (list1['times']>10)]
print(x)
x.to_csv(r'C:\Users\Administrator\Desktop\gg2.csv')