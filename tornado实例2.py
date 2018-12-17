
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import tornado
from tornado.gen import coroutine, sleep, multi
from tornado.httpclient import AsyncHTTPClient

# -------------------------------------------------- use tornado -------------------------------------------------------

ioloop = tornado.ioloop.IOLoop()

def _stop(future):
    ioloop.stop()

def run_until_complete(future, ioloop=ioloop):
    """Keep running untill the future is done"""
    ioloop.add_future(future, _stop) 
    ioloop.start()

# ---------------------------------------------------------------------------------------------------------------------

@coroutine
def producer1():
    print('---------1')
    yield sleep(3)
    print('---------2')
    yield sleep(2)
    print('---------1')

@coroutine
def producer2():
    print('---------4')
    yield sleep(5)
    print('---------5')
    yield sleep(5)
    print('---------6')

@coroutine
def producer3():
    print('---------7')
    yield sleep(4)
    print('---------8')
    yield sleep(1)
    print('---------9')

@coroutine
def producer4():
    print('---------start request')
    http_client = AsyncHTTPClient()
    res = yield http_client.fetch('http://www.npr.org')
    # res = yield http_client.fetch('test.xxx.com')  # when exception happens, the exception will be eaten inside, not raise to out !?
    print('---------response ok')
    print(res)
    yield sleep(2)
    print('---------haha')

@coroutine
def runner():
    print('--------start--------')
    producer1()  
    producer2()
    producer3()
    producer4()  
    # those coroutines have already started, but not finished, need loop to resume execute later !!
    yield sleep(8)  # change this time to 1/3/5/7/10 to see differency...(when loop stoped, coroutines won't be executed any more)
    print('--------stop--------')

# yield从来只是 ·暂停/挂起· 当前协程
# 是 @coroutine装饰器 内部已经调用了 generator的send方法了,已经将其后的协程扔给loop/或者直接开启某个异步函数在后台执行,
def main():
    run_until_complete(runner())
    ## or
    # run_until_complete(multi([producer1(), producer2(), producer3(), producer4()]))
    pass

main()


