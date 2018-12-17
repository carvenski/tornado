#encoding=utf-8
import tornado.ioloop
import tornado.gen
from tornado.httpclient import AsyncHTTPClient
from tornado.concurrent import Future  #在python里使用tornado的 异步回调函数写法(类似nodejs) 或 协程写法

def asynchronous_fetch():
    # http_client = AsyncHTTPClient()  #关键在于这个函数是异步的
    # def on_response(res):
    #     print('============in callback1=============')
    #     print(res.body[:100])
    #     tornado.ioloop.IOLoop.current().stop()
    # http_client.fetch('http://www.baidu.com', callback=on_response)
    http_client = AsyncHTTPClient()  #关键在于这个函数是异步的
    def on_response(future):
        print('============in callback1=============')
        print(vars(future))
#        tornado.ioloop.IOLoop.current().stop()
    future = http_client.fetch('https://www.github.com') # future此时会向事件队列里注册一个事件(loop会读),并传递异步函数结果到其回调函数
    future.add_done_callback(on_response)
    print('waiting http res then callback1')
    
def asynchronous_test():
    def on_response(future):
        print('============in callback2============')
        print(vars(future))
#       tornado.ioloop.IOLoop.current().stop()
    future = tornado.gen.sleep(3) # 异步非阻塞的sleep
    future.add_done_callback(on_response)  # future此时会向事件队列里注册一个事件(loop会读),并传递异步函数结果到其回调函数
    print('waiting 3s then callback2')

asynchronous_fetch()
asynchronous_test()    

print('loop starting')
tornado.ioloop.IOLoop.current().start()  #libev's eventloop 一定要放在最后一句 ??





