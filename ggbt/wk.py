
import numpy as np

li=[1,2,3,5,8]
#方差 var

li2=[1,2,3,2,1]


x=np.polyfit(range(len(li)),li,deg=1)

d=np.var(li)

print(d)

