import pandas as pd
import numpy as np
import time

List1 = range(1,20,2)
List2 = range(1,60,2)
List3 = range(1,60,2)
List4 = range(1,20,2)

def run(*args):
    cmbty=[]

    # for x in args:what?

    for a in List1:
        for b in List2:
            for c in List3:
                for d in List4:
                    cmbty.append([a,b,c,d])
    return cmbty

def run1(*args):
    cmbty=[]

    # for x in args:what?

    for a in args[0]:
        for b in args[1]:
            for c in args[2]:
                for d in args[3]:
                    cmbty.append([a,b,c,d])
    return cmbty

def run2(*args):
    cmbty=[]

    # for x in args:what?

    for a in args:
        print(a)

    return cmbty

run2(List1,List2)

from sklearn.model_selection import ParameterGrid

param_grid = {'a':List1, 'b': List2,'c': List3,'d': List4}



def ptime(f:str):
    start = time.perf_counter()

    exec(f)

    end = time.perf_counter()

    print(float(end - start))


ptime('run(List1,List2,List3,List4)')
ptime('list(ParameterGrid(param_grid))')
'''
List1 = ['zi', 'qiang', 'xue', 'tang']
List2 = [1, 2]

new_list = []

for m in List1:
    for n in List2:
        new_list.append([m, n])

print(new_list)

'''