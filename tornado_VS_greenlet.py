

from tornado import gen

@gen.coroutine
def fetch_coroutine(url):
    http_client = AsyncHTTPClient()
    response = yield http_client.fetch(url)
    # In Python versions prior to 3.3, returning a value from
    # a generator is not allowed and you must use
    #   raise gen.Return(response.body)
    # instead.
    return response.body


VS


>>> def test1(x, y):
...     z = gr2.switch(x+y)
...     print z
...
>>> def test2(u):
...     print u
...     gr1.switch(42)
...
>>> gr1 = greenlet(test1)
>>> gr2 = greenlet(test2)
>>> gr1.switch("hello", " world")
hello world


写法不同,原理/理解应该是相同的: ?
##   response = yield http_client.fetch(url)   VS   z = gr2.switch(x+y)






