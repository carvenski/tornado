#encoding=utf-8
import tornado.ioloop
from tornado import gen
from tornado.httpclient import AsyncHTTPClient  #在python里使用tornado的 异步回调函数写法(类似nodejs) 或 协程写法

'''
!!!! 关于 a = yield b 语法的理解 !!!!
res = yield http_client.fetch('https://www.github.com/yxzoro')  

yield这一句真正的理解其实等价于下面的写法:

yield future = http_client.fetch('https://www.github.com/yxzoro') (yield后面的函数返回的结果(future)会被返回到外面调用者那里,yield是往外传结果的)
do something with res (这里的res其实是loop在下一次跳回到该协程这里时传入的future里的结果,本质上应该就是使用send(arg)函数传参数进协程)

-------------------------------------------!!!! 关于 res = yield some_coroutine_function() 语法的理解 !!!!-------------------------------------------------------------------------------
res = yield some_coroutine_function()  
等价于 
furute = some_coroutine_function()
res = yield future  

例如： res = yield http_client.fetch('https://www.github.com/yxzoro')  
http_client.fetch本身就是个tornado提供的异步的协程函数,该协程函数被调用时： 
    首先执行了该协程(@coroutine装饰器内部开启执行),然后立即返回一个future对象,然后由yield暂时离开/挂起当前的协程函数而转到调用者函数那里(loop调度器)
    yield后面跟的值会一起被返回给调用者,然后当http_client.fetch执行完有结果后,就由loop调度者调度回来这里,并带回结果(yield前面的参数接收future结果),
    然后继续·顺序执行· (yield其实就是简化了原先callback风格导致异步代码很好写而顺序代码很难写的问题)
--------------------------------------------------------------------------------------------------------------------------------------------------
'''
@gen.coroutine
def asynchronous_fetch():
    http_client = AsyncHTTPClient()
    print('=====================================1')
    res = yield http_client.fetch('https://www.github.com/yxzoro')  #向事件队列注册异步事件(loop会在io完成后控制再跳回来的),并跳出当前协程,
    print('============in callback1=============')
    print(vars(res))

@gen.coroutine    
def asynchronous_sleep1():
    print('=====================================2')    
    res = yield tornado.gen.sleep(5)  #向事件队列注册异步事件(loop会在io完成后控制再跳回来的),并跳出当前协程,
    print('============in callback2=============')
    print(res)

@gen.coroutine    
def asynchronous_sleep2():
    print('=====================================3')    
    res = yield tornado.gen.sleep(2)  #向事件队列注册异步事件(loop会在io完成后控制再跳回来的),并跳出当前协程,
    print('============in callback3=============')
    print(res)

asynchronous_fetch()
asynchronous_sleep1()
asynchronous_sleep2()   ## 只是把异步回调函数的写法改成了yield的同步写法而已,并发的原理还是类似的,必须基于异步函数+loop,异步回调/协程 不同写法.

print('loop starting')
tornado.ioloop.IOLoop.current().start()  ## ioloop在当前进程运行后就不会关闭(就是个死循环),直到手动关闭 !!



