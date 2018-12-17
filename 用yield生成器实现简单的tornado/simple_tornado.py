# understanding of 
#   python yield/generator
#   tornado coroutine/future
# ------------------------------------------------------
#   realize a simple tornado-like coroutine framework
# ------------------------------------------------------
import threading
import time

class Future(object):

    def __init__(self, done=False, result=None):
        self.done = done
        self.result = result

    def set_result(self, result):
        self.result = result
        self.done = True

    def get_result(self):
        return self.result

    def is_done(self):
        return self.done

def wrap_with_future(func, *args, **kwargs):
    def _func(*args, **kwargs):
        if len(kwargs) == 1:
            r = func(*args)
        else:
            r = func(*args, **kwargs)
        if func.__name__ == 'sleep':
            r = 'return from sleep ' + str(args[0])
        kwargs['__future'].set_result(r)
        return r
    f = Future()
    kwargs['__future'] = f
    # run sync func in a new thread
    t = threading.Thread(target=_func, args=args, kwargs=kwargs)
    t.start()
    return f

def f1(a, b):
    print('in f1 1 time, init args = ', a, b)
    r = yield wrap_with_future(time.sleep, 3)
    print('in f1 2 time, with args = ', r)
    r = yield wrap_with_future(time.sleep, 2)
    print('in f1 3 time, with args = ', r)
    yield Future(True, 'return 3 from f1, byebye ...')

def f2(a, b):
    print('in f2 1 time, init args = ', a, b)
    r = yield wrap_with_future(time.sleep, 1)
    print('in f2 2 time, with args = ', r)
    r = yield wrap_with_future(time.sleep, 2)
    print('in f2 3 time, with args = ', r)
    yield Future(True, 'return 3 from f2, byebye ...')

def scheduler(g_list=[]):
    futures = []
    # start all generators
    for g in g_list:        
            f = g.next()
            futures.append([f, g])
    # waiting for all futures done
    t1 = time.time()
    while futures:
        for index, i in enumerate(futures):
            f = i[0]; g = i[-1]
            if not f:
                pass
            else:
                if f.is_done():
                    r = f.get_result()
                    try:
                        _f = g.send(r)
                        futures[index][0] = _f
                    except StopIteration: 
                        futures[index][0] = None
        if time.time() - t1 > 10:
            print('... loop heartbeat ...')
            t1 = time.time()

if __name__ == '__main__':
    scheduler([f1(1, 2), f2(3, 4)])




