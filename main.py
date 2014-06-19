import tornado.ioloop
import config

from ctrls.web import web_handlers
from ctrls.api import api_handlers


handlers = web_handlers + api_handlers

if config.DEBUG:
    handlers += [
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"})
    ]

application = tornado.web.Application(
    handlers,
    debug=config.DEBUG,
    cookie_secret=config.COOKIE_SECRET,
    xsrf_cookies=True,
    login_url='/login',
    template_path='templates',
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
