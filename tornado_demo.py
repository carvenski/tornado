

'''
摘要: Tornado(龙卷风)是一个Python Web框架和异步网络库，最初由​FriendFeed开发。通过使用非阻塞网络I/O，
Tornado可以扩展到打成千上万的连接，使其很适合long polling, WebSocket等需要每个用户保持活动连接的应用。
'''

# 快速入门

import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world\n")

application = tornado.web.Application([(r"/", MainHandler),])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

# 用浏览器或者curl等访问http://localhost:8888/，会返回"Hello, world"。

# 服务器端执行
# $ python test.py 
# WARNING:tornado.access:404 GET /favicon.ico (127.0.0.1) 0.81ms
# WARNING:tornado.access:404 GET /favicon.ico (127.0.0.1) 0.81ms
# # 客户端执行
# $ curl  
# Hello, world
# 这个例子没有用到Tornado的异步功能，异步的实例参见chatdemo.py

# Introduction-to-Tornado中介绍的实例稍微复杂点：

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        greeting = self.get_argument('greeting', 'Hello')
        self.write(greeting + ', friendly user!')

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/", IndexHandler)])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

# 执行结果：

# # 服务器端执行
# $ python hello.py --port=8000
# [I 150525 08:41:53 web:1825] 200 GET / (127.0.0.1) 0.85ms
# [I 150525 08:42:26 web:1825] 200 GET /?greeting=Salutations (127.0.0.1) 0.68ms
# # 客户端执行
# $ curl http://localhost:8000/
# Hello, friendly user!
# $ curl http://localhost:8000/?greeting=Salutations
# Salutations, friendly user!
# 这里增加了tornado.options.parse_command_line()用于解析http参数。上例中用application.listen(8888)直接启动http服务，
# 这里改为用tornado.httpserver.HTTPServer启动。

# Introduction-to-Tornado中字符串实例如下：

import textwrap

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
            
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class ReverseHandler(tornado.web.RequestHandler):
    def get(self, input):
        self.write(input[::-1] + '\n')

class WrapHandler(tornado.web.RequestHandler):
    def post(self):
        text = self.get_argument('text')
        width = self.get_argument('width', 40)
        self.write(textwrap.fill(text, int(width)) + '\n')

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[
        (r"/reverse/(\w+)", ReverseHandler),
        (r"/wrap", WrapHandler)
    ])

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

# 执行结果：

# # 服务器端执行
# $ python string_service.py --port=8000
# [I 150525 09:01:18 web:1825] 200 GET /reverse/stressed (127.0.0.1) 0.56ms
# [I 150525 09:01:24 web:1825] 200 GET /reverse/slipup (127.0.0.1) 0.65ms
# [I 150525 09:01:59 web:1825] 200 POST /wrap (127.0.0.1) 1.89ms
# [I 150525 09:02:14 web:1825] 200 POST /wrap (127.0.0.1) 0.97ms

# # 客户端执行
# $ curl http://localhost:8000/reverse/stressed
# desserts
# $ curl http://localhost:8000/reverse/slipup
# pupils
# $ curl http://localhost:8000/wrap -d text=Lorem+ipsum+dolor+sit+amet,+consectetuer+adipiscing+elit.Lorem ipsum dolor sit amet, consectetuer
# adipiscing elit.
# $ curl http://localhost:8000/wrap -d text=hello
# hello
# 在上面的代码中，Application类在"handlers"参数中实例化了两个RequestHandler类对象。

# "/reverse/(\w+)"中，正则表达式告诉Tornado匹配任何以字符串/reverse/开始并紧跟着一个或多个字母的路径。
# 括号的含义是 让Tornado保存匹配括号里面表达式的字符串，并将其作为请求方法的一个参数传递给RequestHandler类。
# “get(self, input):”中有一个额外的参数input。这个参数将包含匹配处理函数正则表达式第一个括号里的字符串, 
# 如果正则表达式中有一系列额外的括号，匹配的字符串将被按照在正则表达式中出现的顺序作为额外的参数传递进来。

# WrapHandler类处理匹配路径为/wrap的请求。这个处理函数定义了一个post方法，也就是说它接收HTTP的POST方法的请求。
# Tornado可以解析URLencoded和multipart结构的POST请求。

# 常见的读写数据库可以结合post和get实现，比如(非实际可执行的例子):

# matched with (r"/widget/(\d+)", WidgetHandler)class WidgetHandler(tornado.web.RequestHandler):
    def get(self, widget_id):
        widget = retrieve_from_db(widget_id)
        self.write(widget.serialize())

    def post(self, widget_id):
        widget = retrieve_from_db(widget_id)
        widget['foo'] = self.get_argument('foo')
        save_to_db(widget)

# HTTP请求（GET、POST、PUT、DELETE、HEAD、OPTIONS）可以非常容易地定义，只需要在RequestHandler类中使用 同名的方法。
# 下面是另一个想象的例子，在这个例子中针对特定frob ID的HEAD请求只根据frob是否存在给出信息，而GET方法返回整个对象：

# matched with (r"/frob/(\d+)", FrobHandler)class FrobHandler(tornado.web.RequestHandler):
    def head(self, frob_id):
        frob = retrieve_from_db(frob_id)
        if frob is not None:
            self.set_status(200)
        else:
            self.set_status(404)

    def get(self, frob_id):
        frob = retrieve_from_db(frob_id)
        self.write(frob.serialize())

# 使用RequestHandler类的set_status()方法显式地设置HTTP状态码。然而，你需要记住在某些情况下，Tornado会自动地设置HTTP状态码。下面是一个常用情况的纲要：

# 404 Not Found: Tornado会在HTTP请求的路径无法匹配任何RequestHandler类相对应的模式时返回404（Not Found）响应码。

# 400 Bad Request: 如果你调用了一个没有默认值的get_argument函数，并且没有发现给定名称的参数，Tornado将自动返回一个400（Bad Request）响应码

# 405 Method Not Allowed: 如果传入的请求使用了RequestHandler中没有定义的HTTP方法（比如，一个POST请求，
# 但是处理函数中只有定义了get方 法），Tornado将返回一个405（Methos Not Allowed）响应码。

# 500 Internal Server Error: 当程序遇到任何不能让其退出的错误时，Tornado将返回500（Internal Server Error）响应码。
# 你代码中任何没有捕获的异常也会导致500响应码。

# 200 OK: 如果响应成功，并且没有其他返回码被设置，Tornado将默认返回一个200（OK）响应码。

# 错误发生时Tornado将默认向客户端发送一个包含状态码和错误信息的简短片段。 
# 可以在你的RequestHandler重载write_error方法自定义错误信息，比如:

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        greeting = self.get_argument('greeting', 'Hello')
        self.write(greeting + ', friendly user!')
        
    def write_error(self, status_code, **kwargs):
        self.write("Gosh darnit, user! You caused a {0} error.\n".format(
            status_code))

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/", IndexHandler)])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

# 执行结果：

# # 服务器端执行
# $ python hello-error.py --port=8000
# [W 150525 09:58:29 web:1825] 405 POST / (127.0.0.1) 1.39ms

# # 客户端执行
# $ curl -d foo=bar http://localhost:8000/
# Gosh darnit, user! You caused a 405 error.
# 安装

# 自动安装：

# # pip install tornado
# PyPI中包含Tornado，可以通过pip或easy_install来安装。这种方式没有包含源代码中的demo程序，下载的源码包可以解决该问题。

# 手动安装:

# # wget https://pypi.python.org/packages/source/t/tornado/tornado-4.1.tar.gz
# # tar xvzf tornado-4.1.tar.gz
# # cd tornado-4.1
# # python setup.py build
# # sudo python setup.py install
# 预置条件：Tornado支持Python2.6、2.7、3.2、3.3和3.4。依赖certifi，Python 2还依赖backports.ssl_match_hostname，
# pip或easy_install自动安装依赖。有些Tornado特性可能依赖以下库：

# unittest2: 在Python2.6执行test suite需要。

# concurrent.futures: Tornado推荐的线程池，允许使用ThreadedResolver。Python 2需要，Python3中标准库已经包含该功能。

# pycurl：tornado.curl_httpclient中选择是否使用。要求用7.18.2或更高版本，建议7.21.1或更高版本。

# twisted: tornado.platform.twisted类可能用到。

# pycares: 当线程是不适合时用作非阻塞DNS解析器。

# Monotime: 增加单调时钟，在时钟调整频繁环境中提高可靠性。在Python 3.3不再需要。

# 平台：Tornado运行在类unix平台，最佳的性能和扩展性体现在Linux(epoll)和BSD(kqueue)




