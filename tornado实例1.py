
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
https://movoto.atlassian.net/browse/DATA-1545
"""

from __future__ import unicode_literals
import logging
import sys
sys.path.append('..')

from tars.aio import coroutine, run_until_complete, wrapper, Queue, SqlHelper, wait, sleep, Event
from tars.options import options as opt
from tars.decorator import debug_wrapper
from Utilities.movoto.logger import MLogger


@coroutine
@wrapper
def producer1(db, queue1):
    try:
        i = 0
        while 1:
            print 'producer1 producing'
            yield sleep(3)
            if i > 10:
                opt.producer1_producing = False
                print 'producer1 stop producing'
                break

            print 'producer1 putting goods into queue1'
            yield queue1.put(['test'])
            i += 1
    except Exception as err:
        opt.logger.exception(err)
        opt.producer1_producing = False


@coroutine
@wrapper
def consumer1(db, queue1, queue2):
    # ==> 白白调试了很长时间,自己粗心大意了,连条件都没看清楚,or搞成and了 !! 
    while opt.producer1_producing or not queue1.empty():  
        if queue1.empty():
            print 'cousumer1 found queue1 empty'
            yield sleep(1)
            continue

        yield queue1.get()
        print 'consumer1 consumering'
        yield sleep(2)
        print 'consumer1(producer2) putting goods into queue2'
        yield queue2.put(['test'])

    opt.producer2_producing = False
    print 'producer1 stop producing & queue1 is empty'


@coroutine
@wrapper
def consumer2(queue2, db):
    while opt.producer2_producing or not queue2.empty():
        if queue2.empty():
            print 'cousumer2 found queue2 empty'
            yield sleep(1)
            continue

        print 'consumer2 getting goods from queue2'
        yield queue2.get()

        print 'consumer2 consumering'
        yield sleep(2)
    print 'producer2 stop producing & queue2 is empty'

@coroutine
@wrapper
def runner():
    queue1 = Queue(20)
    queue2 = Queue(20)
    movotodb = SqlHelper('movoto', use_connection_pool=True)

    opt.set_option('producer1_producing', True)
    opt.set_option('producer2_producing', True)

    '''
    这3句在@coroutine装饰器内部其实已经开启了协程,
    后面再yield它们只是为了让此处的runner入口协程要等待它们所有协程都完成,才能关闭loop !!!
    '''
    f1 = producer1(movotodb, queue1)
    f2 = wait([consumer1(movotodb, queue1, queue2) for _ in range(5)])  # wait只是把多个协程打包成一个协程
    f3 = consumer2(queue2, movotodb)

    # yield从来只是 ·暂停/挂起· 当前协程
    # 是 @coroutine装饰器 内部已经调用了 generator的send方法了,已经将其后的协程扔给loop/或者直接开启某个异步函数在后台执行,
    yield wait([f3,f2,f1])  #这一句的yield其实是要等到  所有的协程 都执行完了之后 才能停掉loop!否则会导致有协程未执行!

    ''' laisiky原先的写法是为了在每一层的生产者结束时顺序地设置锁也结束以让下一层消费者知道上一层已停止.
    print '--------------yield f2----------------'
    yield f2
    opt.producer2_producing = False  ## 
    print '--------------yield f1 f3----------------'
    yield wait([f1, f3])
    '''

def main():
    #使用一个入口协程(但需要在里面yield所有其他协程执行完毕才行) 或者 直接 传入所有协程 都可以的 
    run_until_complete(runner()) 

def setup_settings():
    if opt.debug:
        opt.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    opt.add_argument('--debug', default=False, action='store_true')
    opt.add_argument('--start_pid', type=str, default='0')
    opt.add_argument('--siloing_states', action='append', default=['NJ','IL','MI','FL','KY','MD','NC','TN','WA'])
    opt.parse_args()

    opt.set_option('logger', MLogger().getLogger('fix_wrong_url_property', ''))

    setup_settings()
    main()

