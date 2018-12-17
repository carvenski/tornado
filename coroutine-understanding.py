# 1:use yield to switch in multi coroutine (like greenlet.switch):
# 2:then, we need to return from a function in a coroutine immediately(Async function/return a Future placeholder first),
#   so we can switch to another coroutine to continue execute code.

def c1():
    print('in co1.1')
    # do Async http here
    yield x2.next()

def c2():
    print('in co2')
    # do Async http here
    yield x3.next()

def c3():
    print('in co3')
    # do Async http here

x1 = c1(); x2 = c2(); x3 = c3()
x1.next() # 此处可以实现一个控制器函数(传入所有的协程)来调度所有的协程间的跳转-->跳转依据就是能够判断出当前协程阻塞了 !!

# 以上的函数跳转功能(yield/greenlet.switch)只需再加上一项即可实现并发了:
# 原本一个阻塞的函数需要立即返回一个占位符(tornado的Future),然后才可以执行yield/greenlet.switch来跳转到下一个协程 !!

# 异步函数和同步函数的区别就是:是否是立即返回一个占位符的,以让当前代码继续向下执行,而不是必须等待到返回结果才能继续向下走.
# 所以协程并发的实现必须要有'异步函数'的支持,那个协程中调用的'阻塞的函数必须换成异步非阻塞的函数'  是吗????

# 几个概念的区分: 异步/同步  协程  并发
# 协程归协程,异步归异步,这是2个不同的概念,只是它们俩组合到一起使用时,就可以实现了 并发执行效果了
# (异步本身就可以使用 回调函数的写法来实现并发,只是协程的写法对于顺序逻辑更好写而已.)

# ------------------------------------------------------------------------------------------------------------------------------
# 协程和异步回调 2种写法都能实现 并发效果,只是对于一个独立的子任务里面的顺序逻辑代码的写法上,协程更加好写,而回调则不适合顺序逻辑.
# 正如tornado里面的 @asynchronous 和 @coroutine 的区别一样
# ------------------------------------------------------------------------------------------------------------------------------


