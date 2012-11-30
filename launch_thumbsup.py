#!/usr/bin/env python
import os
import logging
from functools import partial

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.process

from thumbsup import ThumbnailHandler
import thumbsup.paths
from settings import settings

# If setproctitle is installed, set the process title to 'thumbsup'
try:
    import setproctitle
    setproctitle.setproctitle("thumbsup")
except ImportError:
    pass


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


def check_config_sanity():
    allowed_formats = ("png", "jpg", "gif")
    assert settings["image_format"].lower() in allowed_formats
    assert os.path.isdir(settings["static_path"])
    assert os.path.isfile(settings["phantomjs_path"])


if __name__ == "__main__":
    tornado.options.parse_command_line()

    check_config_sanity()

    try:
        http_server = tornado.httpserver.HTTPServer(init_application(),
                                                    xheaders=True)
        http_server.bind(settings["port"])
        http_server.start(settings["processes"])
        task_id = tornado.process.task_id()
        if task_id is None:
            logging.info("Initialized. Starting server")
        else:
            logging.info("Initialized. Starting instance %d" % task_id)

        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info("IOLoop terminated by user")
    except Exception as e:
        logging.error("IOLoop terminated with: %s" % e)
