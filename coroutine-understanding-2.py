

import tornado.gen
import greenlet
from greenlet import greenlet
import time

def test1():
    print('================1')
    x = tornado.gen.sleep(10) # 异步非阻塞的sleep
    print(x)
    gr2.switch()
    print('================3')

def test2():
    print('================2')
    gr1.switch()
    
gr1 = greenlet(test1)
gr2 = greenlet(test2)
gr1.switch()


    
