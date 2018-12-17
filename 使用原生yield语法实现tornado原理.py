

参考: http://python.jobbole.com/85117/
     http://blog.nathon.wang/2015/06/24/tornado-source-insight-01-gen/

# Generator Coroutines

    # 本文默认读者对 Python 生成器 有一定的了解，不了解者请移步至生成器 – 廖雪峰的官方网站。
    # 本文基于 Python 3.5.1，文中所有的例子都可在 Github(https://github.com/hsfzxjy/python-generator-coroutine-examples) 上获得。

"""
学过 Python 的都知道，Python 里有一个很厉害的概念叫做 生成器（Generators）。一个生成器就像是一个微小的线程，可以随处暂停，也可以随时恢复执行，
还可以和代码块外部进行数据交换。
恰当使用生成器，可以极大地简化代码逻辑。
也许，你可以熟练地使用生成器完成一些看似不可能的任务，如“无穷斐波那契数列”，并引以为豪，认为所谓的生成器也不过如此——那我可要告诉你：这些都太小儿科了，
下面我所要介绍的绝对会让你大开眼界。

生成器 可以实现 协程，你相信吗？
什么是协程

在异步编程盛行的今天，也许你已经对 协程（coroutines） 早有耳闻，但却不一定了解它。我们先来看看 Wikipedia 的定义：

    Coroutines are computer program components that generalize subroutines for nonpreemptive multitasking, 
    by allowing multiple entry points for suspending and resuming execution at certain locations.

也就是说：协程是一种 允许在特定位置暂停或恢复的子程序——这一点和 生成器 相似。但和 生成器 不同的是，协程 可以控制子程序暂停之后代码的走向，
而 生成器 仅能被动地将控制权交还给调用者。

协程 是一种很实用的技术。和 多进程 与 多线程 相比，协程 可以只利用一个线程更加轻便地实现 多任务，将任务切换的开销降至最低。和 回调 等其他异步技术相比，
协程 维持了正常的代码流程，
在保证代码可读性的同时最大化地利用了 阻塞 IO 的空闲时间。它的高效与简洁赢得了开发者们的拥戴。
Python 中的协程

早先 Python 是没有原生协程支持的，因此在 协程 这个领域出现了百家争鸣的现象。主流的实现由以下两种：

    用 C 实现协程调度。这一派以 gevent 为代表，在底层实现了协程调度，并将大部分的 阻塞 IO 重写为异步。
    用 生成器模拟。这一派以 Tornado 为代表。Tornado 是一个老牌的异步 Web 框架，涵盖了五花八门的异步编程方式，其中包括 协程。
    本文部分代码借鉴于 Tornado。

直至 Python 3.4，Python 第一次将异步编程纳入标准库中（参见 PEP 3156），其中包括了用生成器模拟的 协程。而在 Python 3.5 中，
Guido 总算在语法层面上实现了 协程（参见 PEP 0492）。
比起 yield 关键字，新关键字 async 和 await 具有更好的可读性。在不久的将来，新的实现将会慢慢统一混乱已久的协程领域。

尽管 生成器协程 已成为了过去时，但它曾经的辉煌却不可磨灭。下面，让我们一起来探索其中的魔法。
一个简单的例子

假设有两个子程序 main 和 printer。printer 是一个死循环，等待输入、加工并输出结果。main 作为主程序，不时地向 printer 发送数据。

这应该怎么实现呢？
"""

# 传统方式中，这几乎不可能在一个线程中实现，因为死循环会阻塞。而协程却能很好地解决这个问题：
def printer():

    counter = 0
    while True:
        string = (yield)
        print('[{0}] {1}'.format(counter, string))
        counter += 1

if __name__ == '__main__':
    p = printer()
    next(p)
    p.send('Hi')
    p.send('My name is hsfzxjy.')
    p.send('Bye!')
    
def printer(): 
    counter = 0
    while True:
        string = (yield)
        print('[{0}] {1}'.format(counter, string))
        counter += 1
 
if __name__ == '__main__':
    p = printer()
    next(p)
    p.send('Hi')
    p.send('My name is hsfzxjy.')
    p.send('Bye!')

# 输出：
# [0] Hi
# [1] My name is hsfzxjy.
# [2] Bye!

# 这其实就是最简单的协程。程序由两个分支组成。主程序通过 send 唤起子程序并传入数据，子程序处理完后，用 yield 将自己挂起，并返回主程序，如此交替进行。
# 协程调度

# 有时，你的手头上会有多个任务，每个任务耗时很长，而你又不想同步处理，而是希望能像多线程一样交替执行。这时，你就需要一个调度器来协调流程了。

# 作为例子，我们假设有这么一个任务：
def task(name, times):

    for i in range(times):
        print(name, i)
    
# 如果你直接执行 task，那它会在遍历 times 次之后才会返回。为了实现我们的目的，我们需要将 task 人为地切割成若干块，以便并行处理：
def task(name, times):

    for i in range(times):
        yield
        print(name, i)

# 这里的 yield 没有逻辑意义，仅是作为暂停的标志点。程序流可以在此暂停，也可以在此恢复。而通过实现一个调度器，我们可以完成多个任务的并行处理：
from collections import deque

class Runner(object):

    def __init__(self, tasks):
        self.tasks = deque(tasks)

    def next(self):
        return self.tasks.pop()

    def run(self):
        while len(self.tasks):
            task = self.next()
            try:
                next(task)
            except StopIteration:
                pass
            else:
                self.tasks.appendleft(task)

    
from collections import deque
 
class Runner(object):
 
    def __init__(self, tasks):
        self.tasks = deque(tasks)
 
    def next(self):
        return self.tasks.pop()
 
    def run(self):
        while len(self.tasks):
            task = self.next()
            try:
                next(task)
            except StopIteration:
                pass
            else:
                self.tasks.appendleft(task)

# 这里我们用一个队列（deque）储存任务列表。其中的 run 是一个重要的方法： 它通过轮转队列依次唤起任务，并将已经完成的任务清出队列，
# 简洁地模拟了任务调度的过程。
# 而现在，我们只需调用：

Runner([
    task('hsfzxjy', 5),
    task('Jack', 4),
    task('Bob', 6)
]).run()

# 就可以得到预想中的效果了：
# Bob 0
# Jack 0
# hsfzxjy 0
# Bob 1
# Jack 1
# hsfzxjy 1
# Bob 2
# Jack 2
# hsfzxjy 2
# Bob 3
# Jack 3
# hsfzxjy 3
# Bob 4
# hsfzxjy 4
# Bob 5


# 简直完美！答案和丑陋的多线程别无二样，代码却简单了不止一个数量级。
# 异步 IO 模拟

# 你绝对有过这样的烦恼：程序常常被时滞严重的 IO 操作（数据库查询、大文件读取、越过长城拿数据）阻塞，在等待 IO 返回期间，线程就像死了一样，空耗着时间。
# 为此，你不得不用多线程甚至是多进程来解决问题。

# 而事实上，在等待 IO 的时候，你完全可以做一些与数据无关的操作，最大化地利用时间。Node.js 在这点做得不错——它将一切异步化，压榨性能。
# 只可惜它的异步是基于事件回调机制的，稍有不慎，你就有可能陷入 Callback Hell 的深渊。

# 而协程并不使用回调，相比之下可读性会好很多。其思路大致如下：

#     维护一个消息队列，用于储存 IO 记录。
#     协程函数 IO 时，自身挂起，同时向消息队列插入一个记录。
#     通过轮询或是 epoll 等事件框架，捕获 IO 返回的事件。
#     从消息队列中取出记录，恢复协程函数。

# 现在假设有这么一个耗时任务：
    
def task(name):
    print(name, 1)
    sleep(1)
    print(name, 2)
    sleep(2)
    print(name, 3)

# 正常情况下，这个任务执行完需要 3 秒，倘若多个同步任务同步执行，执行时间会成倍增长。而如果利用协程，我们就可以在接近 3 秒的时间内完成多个任务。
# 首先我们要实现消息队列：

events_list = []

class Event(object):

    def __init__(self, *args, **kwargs):
        self.callback = lambda: None
        events_list.append(self)

    def set_callback(self, callback):
        self.callback = callback

    def is_ready(self):
        result = self._is_ready()

        if result:
            self.callback()

        return result

# Event 是消息的基类，其在初始化时会将自己放入消息队列 events_list 中。Event 和 调度器 使用回调进行交互。

# 接着我们要 hack 掉 sleep 函数，这是因为原生的 time.sleep() 会阻塞线程。通过自定义 sleep 我们可以模拟异步延时操作：

# sleep.py
from event import Event
from time import time

class SleepEvent(Event):

    def __init__(self, timeout):
        super(SleepEvent, self).__init__(timeout)
        self.timeout = timeout
        self.start_time = time()

    def _is_ready(self):
        return time() - self.start_time >= self.timeout


def sleep(timeout):
    return SleepEvent(timeout)

# 可以看出：sleep 在调用后就会立即返回，同时一个 SleepEvent 对象会被放入消息队列，经过timeout 秒后执行回调。

# 再接下来便是协程调度了：

# runner.py
from event import events_list

def run(tasks):
    for task in tasks:
        _next(task)

    while len(events_list):
        for event in events_list:
            if event.is_ready():
                events_list.remove(event)
                break


def _next(task):

    try:
        event = next(task)
        event.set_callback(lambda: _next(task)) # 1
    except StopIteration:
        pass

# run 启动了所有的子程序，并开始消息循环。每遇到一处挂起，调度器自动设置回调，并在回调中重新恢复代码流。“1” 处巧妙地利用闭包保存状态。

# 最后是主代码：
from sleep import sleep
import runner

def task(name):
    print(name, 1)
    yield sleep(1)
    print(name, 2)
    yield sleep(2)
    print(name, 3)

if __name__ == '__main__':
    runner.run((task('hsfzxjy'), task('Jack')))

# 输出：
# hsfzxjy 1
# Jack 1
# hsfzxjy 2
# Jack 2
# hsfzxjy 3
# Jack 3
# [Finished in 3.0s]

# 协程函数的层级调用

# 上面的代码有一个不足之处，即协程函数返回的是一个 Event 对象。然而事实上只有直接操纵 IO 的协程函数才有可能接触到这个对象。那么，
# 对于调用了 IO 的函数的调用者，它们应该如何实现呢？

# 设想如下任务：
def long_add(x, y, duration=1):
    yield sleep(duration)
    return x + y


def task(duration):
    print('start:', time())
    print((yield long_add(1, 2, duration)))
    print((yield long_add(3, 4, duration)))

# long_add 是 IO 的一级调用者，task 调用 long_add，并利用其返回值进行后续操作。

# 简而言之，我们遇到的问题是：一个被唤起的协程函数如何唤起它的调用者？

# 正如在上个例子中，协程函数通过 Event 的回调与调度器交互。同理，我们也可以使用一个类似的对象，在这里我们称其为 Future。

# Future 保存在被调用者的闭包中，并由被调用者返回。而调用者通过在其上面设置回调函数，实现两个协程函数之间的交互。

# Future 的代码如下，看起来有点像 Event：

# future.py
class Future(object):
    def __init__(self):
        super(Future, self).__init__()
        self.callback = lambda *args: None
        self._done = False

    def set_callback(self, callback):
        self.callback = callback

    def done(self, value=None):
        self._done = True
        self.callback(value)

# Future 的回调函数允许接受一个参数作为返回值，以尽可能地模拟一般函数。

# 但这样一来，协程函数就会有些复杂了。它们不仅要负责唤醒被调用者，还要负责与调用者之间的交互。这会产生许多重复代码。为了 D.R.Y，我们用装饰器封装这一逻辑：

# co.py
from functools import wraps
from future import Future

def _next(gen, future, value=None):

    try:
        try:
            yielded_future = gen.send(value)
        except TypeError:
            yielded_future = next(gen)

        yielded_future.set_callback(lambda value: _next(gen, future, value))
    except StopIteration as e:
        future.done(e.value)


def coroutine(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        future = Future()

        gen = func(*args, **kwargs)
        _next(gen, future)
        return future

    return wrapper

# 被 coroutine 包装过的生成器成为了一个普通函数，返回一个 Future 对象。_next 为唤醒的核心逻辑，通过一个类似递归的回调设置简洁地实现自我唤醒。
# 当自己执行完时，会将自己闭包内的Future对象标记为done，从而唤醒调用者。

# 为了适应新变化，sleep 也要做相应的更改：
from event import Event
from future import Future
from time import time

class SleepEvent(Event):

    def __init__(self, timeout):
        super(SleepEvent, self).__init__()
        self.start_time = time()
        self.timeout = timeout

    def _is_ready(self):
        return time() - self.start_time >= self.timeout


def sleep(timeout):
    future = Future()
    event = SleepEvent(timeout)
    event.set_callback(lambda: future.done())
    return future

# sleep 不再返回 Event 对象，而是一致地返回 Future，并作为 Event 和 Future 之间的代理者。

# 基于以上更改，调度器可以更加简洁——这是因为协程函数能够自我唤醒：

# runner.py
from event import events_list

def run():
    while len(events_list):
        for event in events_list:
            if event.is_ready():
                events_list.remove(event)
                break

# 主程序：
from co import coroutine
from sleep import sleep
import runner
from time import time

@coroutine
def long_add(x, y, duration=1):
    yield sleep(duration)
    return x + y


@coroutine
def task(duration):
    print('start:', time())
    print((yield long_add(1, 2, duration)), time())
    print((yield long_add(3, 4, duration)), time())

task(2)
task(1)
runner.run()

# 由于我们使用了一个糟糕的事件轮询机制，密集的计算会阻塞通往 stdout 的输出，因而看起来所有的结果都是一起打印出来的。为此，我在打印时特地加上了时间戳，
# 以演示协程的效果。输出如下：
# start: 1459609512.263156
# start: 1459609512.263212
# 3 1459609513.2632613
# 3 1459609514.2632234
# 7 1459609514.263319
# 7 1459609516.2633028

# 这事实上是 tornado.gen.coroutine 的简化版本，为了叙述方便我略去了许多细节，如异常处理以及调度优化，
# 目的是让大家能较清晰地了解 生成器协程 背后的机制。因此，这段代码并不能用于实际生产中。
# 小结

#     这，才叫精通生成器。
#     学习编程，不仅要知其然，亦要知其所以然。
#     Python 是有魔法的，只有想不到，没有做不到。

# References:
#     tornado.gen.coroutine

# 相关文章

#     完全理解 Python 迭代对象、迭代器、生成器 · http://python.jobbole.com/87805/?utm_source=blog.jobbole.com&utm_medium=relatedPosts
#     提高你的Python: 解释 yield 和 Generators（生成器） http://python.jobbole.com/87613/?utm_source=blog.jobbole.com&utm_medium=relatedPosts
#     谈谈Python的生成器  http://python.jobbole.com/87154/?utm_source=blog.jobbole.com&utm_medium=relatedPosts
#     Python 进阶_生成器 & 生成器表达式 ·  http://python.jobbole.com/86606/?utm_source=blog.jobbole.com&utm_medium=relatedPosts
#     可迭代对象 vs 迭代器 vs 生成器  http://python.jobbole.com/86258/?utm_source=blog.jobbole.com&utm_medium=relatedPosts


# 评论
    #     谢谢你的文章，我看到long_add返回了值，我想问，在python2.x中return是不能出现在生成器中的，虽然在python3.x中这样写似乎没什么问题但是请问我如何获得返回的值

    #         py2的兼容方法是: 用raise代替return，raise一个特殊的异常，并将返回值附在异常上，从而将值传出去。详见tornado的Return对象

    # call/cc, yield, coroutine 不本来就是几乎等价的么…每个语言学yield的时候应该都会提到这样的关系
    #     初次接触 coroutine 是玩 Lua 时, 那时的感觉就是 yield, coroutine 几乎就是等价的, 玩 python 时把这两个分开讲, 看完后感觉还是几是等价...

    #     Lua 中通过 coroutine.yield() 将协程挂起...所以脱离 yield, coroutine 根本就无从谈起...pytthon 似乎是在 Lua coroutine 上附加了 Generator 的概念...
    #         其实都是一样的，都是call/cc

