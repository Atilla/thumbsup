#!/usr/bin/env python
import logging
from functools import partial

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from thumbsup import ThumbnailHandler, urlnorm
from settings import settings

ThumbsHandler = partial(ThumbnailHandler, settings=settings)

handlers = [
    (r"/", ThumbsHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler,
     {"path" : settings['static_path']}),
]

application = tornado.web.Application(handlers,
                                      static_path=settings["static_path"])

if __name__ == "__main__":
    tornado.options.parse_command_line()
    rootLogger = logging.getLogger('')
    rootLogger.setLevel(logging.DEBUG)

    try:
        http_server = tornado.httpserver.HTTPServer(application,
                                                    no_keep_alive=True)
        http_server.listen(settings["port"])
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info("IOLoop terminated by user")
    except Exception, e:
        logging.error("IOLoop terminated with: %s" % e)
