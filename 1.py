import threading
import time
from threading import Thread, Lock
from queue import Queue

qu = Queue()

for i in range(100):
    qu.put(i)


def get_info():
    while not qu.empty():
        time.sleep(1)
        print(qu.get(1))


th = []
for i in range(10):
    t = threading.Thread(target=get_info, args=())
    th.append(t)


for i in th:
    i.start()
for i in th:
    i.join()