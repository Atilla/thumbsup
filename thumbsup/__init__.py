"""
thumbsup - a website sreenshot service based on PhantomJS and Tornado
"""
import os
import socket
import subprocess
import logging
from functools import partial
from urlparse import urlparse, urlunparse

import tornado.ioloop
import tornado.web

# If using a new python, import the lru_cache from stdlib otherwise
# use the backported functools module
try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

from thumbsup import urlnorm, calls, paths


@lru_cache(maxsize=100000)
def domain_exists(domain):
    try:
        logging.debug("Checking for existance of non-cached domain")
        return socket.gethostbyname(domain)
    except socket.gaierror:
        logging.error("Domain not found - %s" % domain)
        return None


class TaskChain(object):
    """
    Defines a chain of external calls to be executed in order
    """
    def __init__(self, callback, errback):

        self.commands = []
        self.callbacks = []
        self.callback = callback
        self.errback = errback

        self.callopts = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "close_fds": True,
            }

        self.ioloop = tornado.ioloop.IOLoop.instance()

    def __call__(self):
        assert self.callback
        assert self.errback
        self._execute(None, None, None)

    def attach(self, command, callback):
        self.commands.append(command)
        self.callbacks.append(callback)

    def _execute(self, fd, events, to_call):
        success = True
        if to_call is not None:
            assert self.pipe
            success = to_call(self.pipe)
            logging.debug("Removing handler %s" % fd)
            self.ioloop.remove_handler(fd)

        # Bail if something in the chain breaks
        # or we run out of commands
        if not success:
            self.errback()
            return
        if not self.commands:
            self.callback()
            return

        callargs = self.commands.pop(0)
        nextcall = self.callbacks.pop(0)

        logging.debug("Calling popen")
        self.pipe = subprocess.Popen(callargs, **self.callopts)
        # The handler is the most important bit here. We add the same
        # method as a handler, with the callback for processing the
        # result already passed as the to_call arg.
        logging.debug("Attaching handler to %s " % self.pipe.stdout.fileno())
        self.ioloop.add_handler(self.pipe.stdout.fileno(),
                                partial(self._execute, to_call=nextcall),
                                self.ioloop.ERROR)


class ThumbnailHandler(tornado.web.RequestHandler):

    settings = {}

    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings')

        if "digest" in kwargs:
            self.filename_digest = kwargs.pop("digest")
        else:
            self.filename_digest = paths._simple_digest

        super(ThumbnailHandler, self).__init__(*args, **kwargs)

    @property
    def redirect_location(self):
        return "/static/%s" % (self.filename)

    def _make_external_calls(self, host, destination,
                             view_size, thumb_size, ip):

        # Define the actions for success and failure
        success = partial(self.redirect, self.redirect_location)
        failure = partial(self.send_error, 504)

        fetch_and_resize = TaskChain(success, failure)

        # Phantomjs
        callargs = calls.call_phantom(self.settings["phantomjs_path"],
                                      self.settings["render_script"],
                                      host, destination, view_size,
                                      self.settings["ua_string"], ip)
        logging.debug(callargs)
        fetch_and_resize.attach(callargs, calls.on_phantom)

        # Thumbnail the image
        callargs = calls.call_imagic_resize(destination, thumb_size)
        logging.debug(callargs)
        fetch_and_resize.attach(callargs, calls.on_magic)

        #Start execution
        logging.debug("Handler complete, relaying to async chain")
        fetch_and_resize()

    @tornado.web.asynchronous
    def get(self):
        try:
            host = self.get_argument("host")
            # If we don't have a default scheme, default to http
            # We can't support relative paths anyway.
            components = urlparse(host)
            if not components.scheme:
                components = urlparse("http://" + host)

            components = list(components)
            # Encode the domain according to idna
            domain = components[1].encode("idna")
            components[1] = domain

            if not domain_exists(domain):
                self.send_error(504)
                return
            norm_host = urlunparse(urlnorm.norm(components))
        except (UnicodeError, AttributeError) as e:
            logging.error("Invalid address provided - %s" % host)
            logging.error(e)
            self.send_error(504)
            return

        view_size = self.get_argument("view_size",
                                      self.settings["view_size"]).lower()
        thumb_size = self.get_argument("thumb_size",
                                       self.settings["thumb_size"]).lower()
        image_format = self.get_argument("image_format",
                                         self.settings["image_format"]).lower()

        img_hash = self.filename_digest(domain, norm_host,
                                        view_size, thumb_size)
        self.filename = "%s.%s" % (img_hash, image_format)

        destination = os.path.join(self.settings["static_path"], self.filename)

        if os.path.isfile(destination):
            logging.info("%s exists already, redirecting" % norm_host)
            self.redirect(self.redirect_location)
        else:
            logging.info("%s not found, starting render" % norm_host)
            self._make_external_calls(norm_host, destination,
                                      view_size, thumb_size,
                                      self.request.remote_ip)
