import asyncio

async def create():
        await asyncio.sleep(3.0)
        print("(1) create file")

async def write():
        await asyncio.sleep(1.0)
        print("(2) write into file")
    
async def close():
        print("(3) close file")
    
async def main():
        asyncio.ensure_future(create())
        asyncio.ensure_future(write())
        asyncio.ensure_future(close())
        await asyncio.sleep(5.0)
        #await asyncio.sleep(2.0)
        loop.stop()

loop = asyncio.get_event_loop()   # get loop
asyncio.ensure_future(main())     # add coroutine into loop
loop.run_forever()
print("Pending tasks at exit: %s" % asyncio.Task.all_tasks(loop))
loop.close()


# ------------------------------------------------------------------------------------------------------
""" when you use python3.4/python3.6, you can also use (@asyncio.coroutine/yield from == async/await)
    when you use python2.7, you must use (@tornado.gen.coroutine/yield).

import asyncio

@asyncio.coroutine
def create():
    yield from asyncio.sleep(3.0)
    print("(1) create file")

@asyncio.coroutine
def write():
    yield from asyncio.sleep(1.0)
    print("(2) write into file")

@asyncio.coroutine
def close():
    print("(3) close file")

@asyncio.coroutine
def test():
    asyncio.ensure_future(create())
    asyncio.ensure_future(write())
    asyncio.ensure_future(close())
    yield from asyncio.sleep(5.0)
    #yield from asyncio.sleep(2.0)
    loop.stop()

loop = asyncio.get_event_loop()
asyncio.ensure_future(test())
loop.run_forever()
print("Pending tasks at exit: %s" % asyncio.Task.all_tasks(loop))
loop.close()
"""

