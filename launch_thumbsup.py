#!/usr/bin/env python
import logging
from functools import partial

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from thumbsup import ThumbnailHandler
import thumbsup.paths
from settings import settings


def init_application():
    subfolders = thumbsup.paths.get_subs(settings['static_path'])
    if len(subfolders) < 2:
        ThumbsHandler = partial(ThumbnailHandler, settings=settings)
    else:
        logging.debug("Subfolders found at static_path, using advanced digest")
        digest = thumbsup.paths.consistent_two_level(subfolders)
        ThumbsHandler = partial(ThumbnailHandler, settings=settings,
                                digest=digest)

    handlers = [
        (r"/", ThumbsHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {"path": settings['static_path']}),
        ]

    return tornado.web.Application(handlers,
                                   static_path=settings["static_path"])


if __name__ == "__main__":
    tornado.options.parse_command_line()

    try:
        http_server = tornado.httpserver.HTTPServer(init_application(),
                                                    xheaders=True)
        http_server.listen(settings["port"])

        logging.info("Initialized, Starting server")
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info("IOLoop terminated by user")
    except Exception, e:
        logging.error("IOLoop terminated with: %s" % e)
