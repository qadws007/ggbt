import time
import pip
from subprocess import call
from pip._internal.utils.misc import get_installed_distributions
import threading

list=get_installed_distributions()
s = len(list)
list_name=[i.project_name for i in list]
list_name.remove('pip')



def run(i,n):
    semaphore.acquire()   #加锁
    print("正在执行第 {} 个,名称为： {}".format(str(i),n))
    call("pip install --upgrade " + n, shell=True)
    semaphore.release()     #释放

semaphore = threading.BoundedSemaphore(25)  # 最多允许5个线程同时运行

for i in range(s):
    t = threading.Thread(target=run, args=(i,list_name[i]))
    t.start()

while threading.active_count() != 1:
    pass  # print threading.active_count()
else:
    print('-----all threads done-----')