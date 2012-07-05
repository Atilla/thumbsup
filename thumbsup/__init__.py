"""
thumbsup - a website sreenshot service based on PhantomJS and Tornado
"""
import os
import socket
import subprocess
import logging
import hashlib
from functools import partial
from urlparse import urlparse, urlunparse

import tornado.ioloop
import tornado.web

from thumbsup import urlnorm


class TaskChain(object):
    """
    Defines a chain of external calls to be executed in order
    """
    def __init__(self):

        self.commands = []
        self.callbacks = []
        self.term_callback = None
        self.fail_callback = None

        self.callopts = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "close_fds": True,
            }

        self.ioloop = tornado.ioloop.IOLoop.instance()

    def __call__(self):
        assert self.term_callback
        assert self.fail_callback
        self._execute(None, None, None)

    def attach(self, command, callback):
        self.commands.append(command)
        self.callbacks.append(callback)

    def terminate(self, callback, errback):
        self.term_callback = callback
        self.fail_callback = errback

    def _execute(self, fd, events, to_call):
        success = True
        if to_call is not None:
            assert self.pipe
            success = to_call(self.pipe)
            self.ioloop.remove_handler(fd)

        # Bail if something in the chain breaks
        # or we run out of commands
        if not success:
            self.fail_callback()
            return
        if not self.commands:
            self. term_callback()
            return

        callargs = self.commands.pop(0)
        nextcall = self.callbacks.pop(0)

        self.pipe = subprocess.Popen(callargs, **self.callopts)
        # The handler is the most important bit here. We add the same
        # method as a handler, with the callback for processing the
        # result already passed as the to_call arg.
        self.ioloop.add_handler(self.pipe.stdout.fileno(),
                                partial(self._execute, to_call=nextcall),
                                self.ioloop.READ )


class ThumbnailHandler(tornado.web.RequestHandler):

    settings = {}

    def __init__(self, *args, **kwargs):
        settings = kwargs.pop('settings')
        super(ThumbnailHandler, self).__init__(*args, **kwargs)
        self.settings = settings

    def _make_external_calls(self, host, destination,
                             view_size, thumb_size):

        fetch_and_resize = TaskChain()

        # Phantomjs
        callargs = []
        callargs.append(self.settings["phantomjs_path"])
        callargs.append(self.settings["render_script"])
        callargs.append(host)
        callargs.append(destination)
        x, y = view_size.split('x')
        callargs.append(x)
        callargs.append(y)
        callargs.append("'%s'" % self.settings["ua_string"])
        logging.debug(callargs)
        fetch_and_resize.attach(callargs, self.on_phantom)

        # Crop to viewport size
        callargs = []
        callargs.append("convert")
        callargs.append(destination)
        callargs.append("-crop")
        callargs.append("%s+0+0" % view_size)
        callargs.append(destination)
        logging.debug(callargs)
        fetch_and_resize.attach(callargs, self.on_magic)

        # Thumbnail the image
        callargs = []
        callargs.append("convert")
        callargs.append(destination)
        callargs.append("-filter")
        callargs.append("Lanczos")
        callargs.append("-thumbnail")
        callargs.append(thumb_size)
        callargs.append(destination)
        logging.debug(callargs)
        fetch_and_resize.attach(callargs, self.on_magic)

        success = partial(self.redirect, "/static/%s.png" % self.digest)
        failure = partial(self.send_error, "500")
        fetch_and_resize.terminate(success, failure)

        #Start execution
        fetch_and_resize()

    @tornado.web.asynchronous
    def get(self):

        host = self.get_argument("host")

        # If we don't have a default scheme, default to http
        # We can't support relative paths anyway.
        components = urlparse(host)
        if not  components.scheme:
            components = urlparse("http://" + host)
        norm_host = urlunparse(urlnorm.norm(components))

        try:
            socket.gethostbyname(components.netloc)
        except:
            self.send_error(504)
            return

        view_size = self.get_argument("view_size",
                                      self.settings["view_size"])
        thumb_size = self.get_argument("thumb_size",
                                       self.settings["thumb_size"])

        item_hash = hashlib.md5(norm_host + view_size + thumb_size)
        self.digest = item_hash.hexdigest()
        destination = "%s/%s.png" % (self.settings["static_path"], self.digest)

        if os.path.isfile(destination):
            logging.info("%s exists already, redirecting"  % norm_host)
            self.redirect("/static/%s.png" % self.digest)
        else:
            self._make_external_calls(norm_host, destination,
                                      view_size, thumb_size)

    @classmethod
    def on_phantom(self, pipe):
        """
        Callback for the phantomjs call
        """
        success = True
        for line in pipe.stdout:
            # Expect log output to be prefixed with LOGLEVEL:
            if ":" in line[:10]:
                level, message = line.strip().split(":", 1)
                level = level.upper()
                line = line.strip()
                logging.log(getattr(logging, level, 20), message)
                if level in ("ERROR", "CRITICAL"):
                    success = False
            else:  # Default to info logging
                logging.info(line)

        return success

    @classmethod
    def on_magic(self, pipe):
        """
        Callback for the imagemagic call
        """
        success = True
        for line in pipe.stdout:
            logging.error(line.strip())
            success = False
        if success:
            logging.info("Imagemagic resize success")

        return success
