import time
import threading






def run(n):
    semaphore.acquire()   #加锁
    time.sleep(1)
    print("run the thread:%s\n" % n)
    semaphore.release()     #释放


num = 0
semaphore = threading.BoundedSemaphore(5)  # 最多允许5个线程同时运行

for i in range(10):
    t = threading.Thread(target=run, args=("t-%s" % i,))
    t.start()

while threading.active_count() != 1:
    pass  # print threading.active_count()
else:
    print('-----all threads done-----')