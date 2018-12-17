Techie Blog

ArticlesCode hicking
Understanding the code inside Tornado, the asynchronous web server
Sat 19 September 2009
By admin
In Code hicking.
tags: asynccodehikepythontornadotornadowebwebserver
My goal here is to have a walk through the lower layers of the Tornado
asynchronous web server. I take a bottom-up approach, starting with the
polling loop and going up to the application layer, pointing out the interesting
things I see on my way.

So if you plan on reading the source code of the Tornado web
framework, or you are just curious to see how an asynchronous web server works, I
would love to be your guide.

After reading this, you will:

be able to write the server part of Comet applications, even if you have
to do it from scratch
have a better understanding of the Tornado web framework, if you plan do develop
on it
have a bit more informed opinion in the tornado-twisted debate
Intro

I'll start with a few words of introduction to the Tornado
project, in case you have no idea what it is and why you might be interested in it.
If you're already interested in it, just jump to the next section.

Tornado is a asynchronous http server and web
framework written in Python. It is the framework that powers the FriendFeed website, recently acquired by Facebook. FriendFeed has quite
a few users and many
real-time features, so performance and scalability must have high priorities there.
Since it is open source now (kudos to Facebook), we can all have a look inside it
to see how it works.

I also feel obliged to talk a bit on nonblocking IO or asynchronous IO (AIO) .
If you already know what it is, goto next_section. I'll try to demonstrate it
with a simple example.

Let's suppose you're writing an application that has to query another server
for some data (the database for example, or some sort of remote API) and it's
known that this query can take a long time. Let's say, 5 seconds.
In many web frameworks the handler would look something like:

1
2
3
def handler_request(self, request):
    answ = self.remote_server.query(request) # this takes 5 seconds
    request.write_response(answ)
If you do this in a single thread, you will serve one client every 5 second. During
the five secs, all other have to wait, so you're serving clients with a whooping
rate of 0.2 requests per second. Awesome!

Of course, nobody is that naive, so most will use a multi-threaded server to be able
to support more clients at once. Lets say you have 20 threads.
You improved performance 20 times, so the rate is now 4 request per
second. Still, way too small.
You can keep throwing threads at the problem, but threads are expensive in terms of
memory usage and scheduling.
I doubt you'll ever reach hundreds of requests per second this way.

With AIO, however, thousands of such requests per second are a breeze. The handler
has to be changed to look something like this:

1
2
3
4
5
def handler_request(self, request):
    self.remote_server.query_async(request, self.response_received)

def response_received(self, request, answ):    # this is called 5 seconds later
    request.write(answ)
The idea is that we're not blocking while waiting for the answer to come. Instead,
we give the framework a callback function to call us when the answer has come.
In the mean time, we're free to serve other clients.

This is also the downside of AIO: the code will be a bit... well, twisted. Also, if
you're in a single threaded AIO server like Tornado, you have to be careful never
to block, because all the pending requests will be delayed by that.

A great resource to learn more (than this over simplistic intro) about asynchronous IO
is The C10K problem page.

Source code

The project is hosted at github.
You can get it, although you don't need it for reading this article, with:

git clone git://github.com/facebook/tornado.git
The tornado subdirectory contains a .py file for each of the modules so you
can easily identify them if you have a checkout of the repository.
In each source file, you will find at least one large doc string explaining the module,
and giving an example or two on how to use it.

IOLoop

Lets go directly into the core of the server and look at the
ioloop.py file.
This module is the heart of the asynchronous mechanism. It keeps a list of the
open file descriptors and handlers for each. Its job is to select the ones that are
ready for reading or writing and call the associated handler.

To add a socket to the IOLoop, the application calls the add_handler() method:

1
2
3
4
def add_handler(self, fd, handler, events):
    """Registers the given handler to receive the given events for fd."""
    self._handlers[fd] = handler
    self._impl.register(fd, events | self.ERROR)
The _handlers dictionary maps the file descriptor with the function to be called
when the file descriptor is ready (handler in Tornado terminology).
Then, the descriptor is registered to the epoll list. Tornado cares about three
types of events: READ, WRITE and ERROR. As you can see, ERROR is automatically
added in for you.

The self._impl is an alias to either select.epoll() or select.select(). We'll see how it chooses between them a bit later.

Now lets see the actual main loop, somehow weirdly placed in the start() method:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
def start(self):
    """Starts the I/O loop.

    The loop will run until one of the I/O handlers calls stop(), which
    will make the loop stop after the current event iteration completes.
    """
    self._running = True
    while True:

    [ ... ]

        if not self._running:
            break

        [ ... ]

        try:
            event_pairs = self._impl.poll(poll_timeout)
        except Exception, e:
            if e.args == (4, "Interrupted system call"):
                logging.warning("Interrupted system call", exc_info=1)
                continue
            else:
                raise

        # Pop one fd at a time from the set of pending fds and run
        # its handler. Since that handler may perform actions on
        # other file descriptors, there may be reentrant calls to
        # this IOLoop that update self._events
        self._events.update(event_pairs)
        while self._events:
            fd, events = self._events.popitem()
            try:
                self._handlers[fd](fd, events)
            except KeyboardInterrupt:
                raise
            except OSError, e:
                if e[0] == errno.EPIPE:
                    # Happens when the client closes the connection
                    pass
                else:
                    logging.error("Exception in I/O handler for fd %d",
                                  fd, exc_info=True)
            except:
                logging.error("Exception in I/O handler for fd %d",
                              fd, exc_info=True)
The poll() function returns a dictionary with (fd: events) pairs, stored
in the event_pairs variable. The "Interrupted system call" special case
exception is needed
because the C library poll() function can return EINTR (which has the numerical
value of 4), when a signal comes before any events occurred.
See man poll for details.

The inner while loop takes the pairs from the event_pairs dictionary one by one
and calls the associated handler. The pipe error exception is silenced here. To keep
the generality of this class it would have been perhaps a better idea to catch this
in the http handlers, but it was probably easier like this.

The comment explains why the dictionary had to be parsed using popitem() rather than
the more obvious:

1
for fd, events in self._events.items():
In a nutshell, the dictionary can be modified
during the loop, inside the handlers. See, for example, the removeHandler() function.
The method extracts the fd from the _events dictionary, so that the handler is not
called even if it was selected by the current poll iteration.

1
2
3
4
5
6
7
8
def remove_handler(self, fd):
    """Stop listening for events on fd."""
    self._handlers.pop(fd, None)
    self._events.pop(fd, None)
    try:
        self._impl.unregister(fd)
    except OSError:
        logging.debug("Error deleting fd from IOLoop", exc_info=True)
The (pointless) loop termination trick

A nice trick is how the loop is stopped. The self._running variable is used to break from it
and it can be set to False from the handlers by using the stop() method.
Normally, that would just be the end of it, but
the stop() method might be also called from a signal handler. If 1) the loop is in
poll(), 2) no requests are coming to the server and 3) the signal is not delivered to
the right thread by the OS, you would have to wait for the poll to
timeout. Considering how unlikely this is and that poll_timeout is 0.2 seconds by default,
that's hardly a tragedy, really.

But anyway, to do it they use an anonymous pipe with one end in the set of polled file descriptors. When terminating,
it writes something on the other end, effectively waking up the loop from poll.
Here is the selected code for it:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
def __init__(self, impl=None):

    [...]

    # Create a pipe that we send bogus data to when we want to wake
    # the I/O loop when it is idle
    r, w = os.pipe()
    self._set_nonblocking(r)
    self._set_nonblocking(w)
    self._waker_reader = os.fdopen(r, "r", 0)
    self._waker_writer = os.fdopen(w, "w", 0)
    self.add_handler(r, self._read_waker, self.WRITE)


def _wake(self):
    try:
        self._waker_writer.write("x")
    except IOError:
        pass
In fact, it seems to be a bug in the above code: the read file descriptor r, although
opened for reading, is registered with the WRITE event, which cannot occur. As I said
earlier, it hardly makes a difference so I'm
not surprised that they actually didn't noticed this is not working.
I've pinged
the
mailing list
about this, but I got no answer so far.

Timers

Another nice feature of the IOLoop module is the simple timers implementation. A list of
timers is maintained sorted by expiration time, by using python's bisect
module:

1
2
3
4
5
def add_timeout(self, deadline, callback):
    """Calls the given callback at the time deadline from the I/O loop."""
    timeout = _Timeout(deadline, callback)
    bisect.insort(self._timeouts, timeout)
    return timeout
Inside the main loop, the callbacks from all the expired timers are simply
executed in that order, until the current time is reached. The poll timeout is
adjusted such as the next timer is not delayed if no new requests arrive.

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
self._running = True
while True:
    poll_timeout = 0.2

    [ ... ]
    if self._timeouts:
        now = time.time()
        while self._timeouts and self._timeouts[0].deadline <= now:
            timeout = self._timeouts.pop(0)
            self._run_callback(timeout.callback)
        if self._timeouts:
            milliseconds = self._timeouts[0].deadline - now
            poll_timeout = min(milliseconds, poll_timeout)

[ ... poll ]
Selecting the select method

Let's now have a quick look at the code that selects the poll/select implementation. Python 2.6
has epoll support in the standard library, which is sniffed with hasattr() on the select module.
If on python \< 2.6, Tornado will try to use its on C epoll module. You can find its sources in the
tornado/epoll.c file. Finally, if that fails (epoll is specific to Linux), it will fallback to
selec. _Select and _EPoll classes are wrappers for
emulating the select.epoll API. Before doing your benchmarks, make sure you use epoll, because select
has poor performance with large sets of file descriptors.

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
# Choose a poll implementation. Use epoll if it is available, fall back to
# select() for non-Linux platforms
if hasattr(select, "epoll"):
    # Python 2.6+ on Linux
    _poll = select.epoll
else:
    try:
        # Linux systems with our C module installed
        import epoll
        _poll = _EPoll
    except:
        # All other systems
        import sys
        if "linux" in sys.platform:
            logging.warning("epoll module not found; using select()")
        _poll = _Select
With this, we've covered most of the IOLoop module. As advertised, it is indeed a
nice and simple piece of code.

From sockets to streams

Let's have a look now at the
IOStream module.
Its purpose is to provide a small level of abstraction over nonblocking sockets, by
offering three functions:

read_until(), which reads from the socket until it finds a given string. This is
convenient for reading the HTTP headers until the empty line delimiter.
read_bytes(), which reads a give number of bytes from the socket. This is convenient
for reading the body of the HTTP message.
write() which writes a given buffer to the socket and keeps retrying until the whole
buffer is sent.
All of them can call a callback when they are done, in asynchronous style.

The write() implementation buffers the data provided by the caller and
writes it whenever IOLoop calls its handler, because the socket is ready for writing:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
def write(self, data, callback=None):
    """Write the given data to this stream.

    If callback is given, we call it when all of the buffered write
    data has been successfully written to the stream. If there was
    previously buffered write data and an old write callback, that
    callback is simply overwritten with this new callback.
    """
    self._check_closed()
    self._write_buffer += data
    self._add_io_state(self.io_loop.WRITE)
    self._write_callback = callback
The function that handles the WRITE event simply does socket.send() until EWOULDBLOCK
is hit or the buffer is finished:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
def _handle_write(self):
    while self._write_buffer:
        try:
            num_bytes = self.socket.send(self._write_buffer)
            self._write_buffer = self._write_buffer[num_bytes:]
        except socket.error, e:
            if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                break
            else:
                logging.warning("Write error on %d: %s",
                                self.socket.fileno(), e)
                self.close()
                return
    if not self._write_buffer and self._write_callback:
        callback = self._write_callback
        self._write_callback = None
        callback()
Reading does the reverse process. The read event handler keeps reading until enough
is gathered in the read buffer. This means either it has the required length (if
read_bytes()) or it contains the requested delimiter (if read_until()):

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
def _handle_read(self):
    try:
        chunk = self.socket.recv(self.read_chunk_size)
    except socket.error, e:
        if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
            return
        else:
            logging.warning("Read error on %d: %s",
                            self.socket.fileno(), e)
            self.close()
            return
    if not chunk:
        self.close()
        return
    self._read_buffer += chunk
    if len(self._read_buffer) >= self.max_buffer_size:
        logging.error("Reached maximum read buffer size")
        self.close()
        return
    if self._read_bytes:
        if len(self._read_buffer) >= self._read_bytes:
            num_bytes = self._read_bytes
            callback = self._read_callback
            self._read_callback = None
            self._read_bytes = None
            callback(self._consume(num_bytes))
    elif self._read_delimiter:
        loc = self._read_buffer.find(self._read_delimiter)
        if loc != -1:
            callback = self._read_callback
            delimiter_len = len(self._read_delimiter)
            self._read_callback = None
            self._read_delimiter = None
            callback(self._consume(loc + delimiter_len))
The _consume() function, that is used above, makes sure that no more that what was
requested is taken out of the stream, and subsequent reads will get the immediate
next bytes:

1
2
3
4
def _consume(self, loc):
    result = self._read_buffer[:loc]
    self._read_buffer = self._read_buffer[loc:]
    return result
Also worth noting in the _handle_read() function above is the capping of the
read buffer at self.max_buffer_size. The default value for it is 100MB, which
seems a bit large to me. For example, if an attacker makes just 100 connections
to the server and keeps pushing headers to it without the end headers delimiter,
Tornado will need 10 GB of RAM to serve the requests.
Even if the RAM is not a problem, the copying operations done with a buffer of this size (like in the
_consume() method above) will likely overload the server. Note also how _handle_read()
searches the delimiter in the whole buffer on each iteration, so if the attacker sends
the huge data in small chunks, the server has to do a lot of searches. Bottom of line,
you might want to tune this parameter unless you really expect requests that big and you have
the hardware for it.

The HTTP server

Armed with the IOLoop and IOStream modules, writing an
asynchronous HTTP server is just one step away, and that step is done in
httpserver.py.

The HTTPServer class itself only does the accepting of the new connections by adding
their sockets to the IOLoop. The listening socket itself is part of IOLoop, as seen in
the listen() method:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
def listen(self, port, address=""):
    assert not self._socket
    self._socket = socket.(socket.AF_INET, socket.SOCK_STREAM, 0)
    flags = fcntl.fcntl(self._socket.fileno(), fcntl.F_GETFD)
    flags |= fcntl.FD_CLOEXEC
    fcntl.fcntl(self._socket.fileno(), fcntl.F_SETFD, flags)
    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self._socket.setblocking(0)
    self._socket.bind((address, port))
    self._socket.listen(128)
    self.io_loop.add_handler(self._socket.fileno(), self._handle_events,
                             self.io_loop.READ)
In addition to binding to given address and port, the code above sets the "close on exec"
and "reuse address" flags. The former is useful in the case the application spawns new processes. In
this case, we don't want them to keep the socket open. The latter is useful for avoiding the
"Address already in use" error when restarting the server.

As you can see, the connection backlog is set to 128. This means that if 128 connection are waiting to
be accepted, new connections will be rejected until the server has time to accept some of them.
I suggest trying to increase this one when doing benchmarks, as it directly affects when the new
connections are dropped.

The _handle_events() handler, registered above, accepts the new connection, creates the IOStream
associated with the socket and starts a HTTPConnection class, which is responsible for the
rest of the interaction with it:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
def _handle_events(self, fd, events):
    while True:
        try:
            connection, address = self._socket.accept()
        except socket.error, e:
            if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            raise
        try:
            stream = iostream.IOStream(connection, io_loop=self.io_loop)
            HTTPConnection(stream, address, self.request_callback,
                           self.no_keep_alive, self.xheaders)
        except:
            logging.error("Error in connection callback", exc_info=True)
Note that this method accepts all the pending connections in a single iteration. It stays in
the while True loop until EWOULDBLOCK is returned, which means that there are no more
new connections pending to be accepted.

The HTTPConnection class starts parsing the HTTP headers right in its __init__() method:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
def __init__(self, stream, address, request_callback, no_keep_alive=False,
             xheaders=False):
    self.stream = stream
    self.address = address
    self.request_callback = request_callback
    self.no_keep_alive = no_keep_alive
    self.xheaders = xheaders
    self._request = None
    self._request_finished = False
    self.stream.read_until("\r\n\r\n", self._on_headers)
If you're wondering what xheaders parameter means, see this comment:

If xheaders is True, we support the X-Real-Ip and X-Scheme headers,
which override the remote IP and HTTP scheme for all requests. These
headers are useful when running Tornado behind a reverse proxy or
load balancer.
The _on_headers() callback parses the headers and uses read_bytes() to read the
content of the request, if present. The _on_request_body() callback parses the POST
arguments and then calls the application callback:

 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
def _on_headers(self, data):
    eol = data.find("\r\n")
    start_line = data[:eol]
    method, uri, version = start_line.split(" ")
    if not version.startswith("HTTP/"):
        raise Exception("Malformed HTTP version in HTTP Request-Line")
    headers = HTTPHeaders.parse(data[eol:])
    self._request = HTTPRequest(
        connection=self, method=method, uri=uri, version=version,
        headers=headers, remote_ip=self.address[0])

    content_length = headers.get("Content-Length")
    if content_length:
        content_length = int(content_length)
        if content_length > self.stream.max_buffer_size:
            raise Exception("Content-Length too long")
        if headers.get("Expect") == "100-continue":
            self.stream.write("HTTP/1.1 100 (Continue)\r\n\r\n")
        self.stream.read_bytes(content_length, self._on_request_body)
        return

    self.request_callback(self._request)

def _on_request_body(self, data):
    self._request.body = data
    content_type = self._request.headers.get("Content-Type", "")
    if self._request.method == "POST":
        if content_type.startswith("application/x-www-form-urlencoded"):
            arguments = cgi.parse_qs(self._request.body)
            for name, values in arguments.iteritems():
                values = [v for v in values if v]
                if values:
                    self._request.arguments.setdefault(name, []).extend(
                        values)
        elif content_type.startswith("multipart/form-data"):
            boundary = content_type[30:]
            if boundary: self._parse_mime_body(boundary, data)
    self.request_callback(self._request)
Writing the answer to the request is handled through the HTTPRequest class, which you can
see instantiated in the _on_headers() method above. It just proxies the write to the
stream object.

1
2
3
def write(self, chunk):
    assert self._request, "Request closed"
    self.stream.write(chunk, self._on_write_complete)
To be continued?

With this, I covered all the way from the bare sockets to the application layer.
This should give you a pretty clear image of how Tornado works inside. All in all,
I would say it was a pleasant code hike which I hope you enjoyed as well.

There are still large parts of the framework that remain unexplored,
like wep.py,
which is actually what your application is interacting with, or the template engine.
If there is enough interest, I'll cover those parts as well. Encourage me by subscribing
to my RSS feed.

blogroll
Packetbeat
social
atom feed
Twitter
LinkedIn
Proudly powered by Pelican, which takes great advantage of Python.
The theme is by Smashing Magazine, thanks!
