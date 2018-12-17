

The technology behind Tornado, FriendFeed's web server
September 10, 2009
Today, we are open sourcing the non-blocking web server and the tools that power FriendFeed under the name Tornado Web Server.
We are really excited to open source this project as a part of Facebook's open source initiative, and we hope it will be
useful to others building real-time web services. Check out the announcement on the Facebook Developer Blog. 
You can download Tornado at tornadoweb.org.

Background

While there are a number of great Python frameworks available that have been growing in popularity over the past couple
years (particularly Django), our performance and feature requirements consistently diverged from these mainstream frameworks.
In particular, as we introduced more real-time features to FriendFeed, we needed the support for a large number of standing 
connections afforded by the non-blocking I/O programming style and epoll.

We ended up writing our own web server and framework after looking at existing servers and tools like Twisted because none 
matched both our performance requirements and our ease-of-use requirements.

Tornado looks a bit like web.py or Google's webapp, but with additional tools and optimizations to take advantage of the 
non-blocking web server and tools. Some of the distinctive features of Tornado:

All the basic site building blocks - Tornado comes with built-in support for a lot of the most difficult and tedious aspects
of web development, including templates, signed cookies, user authentication, localization, aggressive static file caching,
cross-site request forgery protection, and third party authentication like Facebook Connect. You only need to use the
features you want, and it is easy to mix and match Tornado with other frameworks.

Real-time services - Tornado supports large numbers of concurrent connections. It is easy to write real-time services 
via long polling or HTTP streaming with Tornado. Every active user of FriendFeed maintains an open connection to 
FriendFeed's servers.

High performance - Tornado is pretty fast relative to most Python web frameworks. We ran some simple load tests against 
some other popular Python frameworks, and Tornado's baseline throughput was over four times higher than the other
frameworks:


Basic usage

The main Tornado module is tornado.web, which implements a lightweight web development framework. 
tornado.web is built on our non-blocking HTTP server and low-level I/O modules. Here is "Hello, world" in Tornado:

import tornado.httpserver
import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
A Tornado web application maps URLs or URL patterns to subclasses of tornado.web.RequestHandler. 
Those classes define get() or post() methods to handle HTTP GET or POST requests to that URL. 
The example above maps the root URL '/' to the MainHandler class, which prints the "Hello, world" message.

All of the additional features of Tornado mentioned above (like localization and signed cookies) are designed to be used
on an à la carte basis. For example, to use signed cookies in your application, you just need to specify the secret cookie
signing key when you create your application:

application = tornado.web.Application([
    (r"/", MainHandler),
], cookie_secret="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=")
and then you can call set_secure_cookie() and get_secure_cookie() in your request handlers:

class LoginHandler(tornado.web.RequestHandler):
    def post(self):
        # Process login username and password
        self.set_secure_cookie("user_id", user["id"])
        self.redirect("/home")
You can find detailed documentation for all of these features at tornadoweb.org/documentation. 
A few of my favorite features are discussed in greater detail below.

Asynchronous requests

Tornado assumes requests are not asynchronous to make writing simple request handlers easy. By default, when a request 
handler is executed, Tornado will finish/close the request automatically.

You can override that default behavior to implement streaming or hanging connections, which are common for real-time 
services like FriendFeed. If you want a request to remain open after the main request handler method, you simply need to 
use the tornado.web.asynchronous decorator:

class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.write("Hello, world")
        self.finish()
When you use this decorator, it is your responsibility to call self.finish() to finish the HTTP request, or the user's
browser will simply hang.

Here is a real example that makes a call to the FriendFeed API using Tornado's built-in asynchronous HTTP client:

class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("http://friendfeed-api.com/v2/feed/bret",
                   callback=self.async_callback(self.on_response))

    def on_response(self, response):
        if response.error: raise tornado.web.HTTPError(500)
        json = tornado.escape.json_decode(response.body)
        self.write("Fetched " + str(len(json["entries"])) + " entries "
                   "from the FriendFeed API")
        self.finish()
When get() returns, the request has not finished. When the HTTP client eventually calls on_response(), the request is still
open, and the response is finally flushed to the client with the call to self.finish().

For a more advanced asynchronous example, take a look at the chat demo application included with Tornado. The chat demo 
uses AJAX and long polling to implement a remedial real-time chat room on Tornado. You can also see the chat demo in action 
on FriendFeed's servers.

Third-party authentication

Tornado comes with built-in support for authenticating with Facebook Connect, Twitter, Google, and FriendFeed in addition to 
OAuth and OpenID. To log a user in via Facebook Connect, you just need to implement a request handler like:

class LoginHandler(tornado.web.RequestHandler, tornado.auth.FacebookMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("session", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()

    def _on_auth(self, user):
        if not user: raise tornado.web.HTTPError(500, "Auth failed")
        self.set_secure_cookie("uid", user["uid"])
        self.set_secure_cookie("session_key", user["session_key"])
        self.redirect("/home")
All of the authentication methods support a relatively uniform interface so you don't need to understand all of the 
intricacies of the different authentication/authorization protocols to leverage them on your site.

See the auth and facebook demo applications included with Tornado for detailed examples of third party authentication.

And more...

Check out the Tornado documentation for a complete list of features and modules.

You can discuss the project, send feedback, and report bugs in our mailing list on Google Groups.


