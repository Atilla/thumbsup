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


class TaskChain(object):
    def __init__(self):

        self.commands = []
        self.callbacks = []

        self.callopts = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "close_fds": True,
            }

        self.ioloop = tornado.ioloop.IOLoop.instance()

    def __call__(self):
        self._execute(None, None, None)

    def attach(self, command, callback):
        self.commands.append(command)
        self.callbacks.append(callback)
        
    def _execute(self, fd, events, to_call):
        success = True
        if to_call is not None:
            assert self.pipe
            success = to_call(self.pipe)
            self.ioloop.remove_handler(fd)

        # Bail if something in the chain breaks
        # or we run out of commands
        if not self.commands or not success:
            return

        callargs = self.commands.pop(0)
        nextcall = self.callbacks.pop(0)
        
        self.pipe = subprocess.Popen(callargs, **self.callopts)
        self.ioloop.add_handler(self.pipe.stdout.fileno(),
                                partial(self._execute, to_call=nextcall),
                                self.ioloop.READ )
        
class ThumbnailHandler(tornado.web.RequestHandler):

    settings = {}

    def __init__(self, *args, **kwargs):
        settings = kwargs.pop('settings')
        super(ThumbnailHandler, self).__init__(*args, **kwargs)
        self.settings = settings

    def _make_external_calls(self, host, destination, width, height):

        chain = TaskChain()

        # Phantomjs
        callargs = []
        callargs.append(self.settings["phantomjs_path"])
        callargs.append(self.settings["render_script"])
        callargs.append(host)
        callargs.append(destination)
        callargs.append(width)
        callargs.append(height)
        callargs.append("'%s'" % self.settings["ua_string"])
        logging.debug(callargs)
        chain.attach(callargs, self.on_phantom)

        callargs = []
        callargs.append("convert")
        callargs.append(destination)
        callargs.append("-crop")
        callargs.append("%sx%s+0+0" %(width, height))
        callargs.append(destination)
        logging.debug(callargs)
        chain.attach(callargs, self.on_magic)

        #Start execution
        chain()


    @tornado.web.asynchronous
    def get(self):

        if 'host' not in self.request.arguments:
            self.send_error(400)
            return
                

        # If we don't have a default scheme, default to http
        # We can't support relative paths anyway.
        components = urlparse(self.request.arguments['host'][0])
        if not  components.scheme:
            components = urlparse("http://"+self.request.arguments['host'][0])
        host = urlunparse(urlnorm.norm(components))

        try:
            socket.gethostbyname(components.netloc)
        except:
            self.send_error(504)
            return


        width = self.settings["size_x"]
        height = self.settings["size_y"]
        
        if "width" in self.request.arguments:
            width = self.request.arguments["width"][0]
        
            
        if "height" in self.request.arguments:
            height = self.request.arguments["height"][0]

        self.digest = hashlib.md5(host).hexdigest()
        destination = "%s/%s.png" % (self.settings["static_path"], self.digest)
        
        if os.path.isfile(destination):
            logging.info("%s exists already, redirecting"  % host)
            self.redirect("/static/%s.png" % self.digest)
        else:
            self._make_external_calls(host, destination, width, height)
            

    def on_phantom(self, pipe):
        """
        Callback for the phantomjs call
        """
        success =  True
        for line in pipe.stdout:
            # Expect log output to be prefixed with LOGLEVEL:
            if ":" in line[:10]:
                level, message = line.strip().split(":",1)
                level = level.upper()
                line = line.strip()
                logging.log(getattr(logging, level, 20), message)
                if level in ("ERROR", "CRITICAL"):
                    success = False
            else: # Default to info logging
                logging.info(line)
        if not success:
            self.send_error(500)

        return success

    def on_magic(self, pipe, terminate=True):
        """
        Callback for the imagemagic call
        """
        success = True
        for line in pipe.stdout:
            logging.error(line.strip())
            success = False
        if success:
            logging.info("Successfully resized %s" % self.digest)
            if terminate:
                self.redirect("/static/%s.png" % self.digest)
        else:
            self.send_error(500)
        
        return success
