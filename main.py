import tornado.ioloop

from ctrls.web import web_handlers
from ctrls.api import api_handlers


application = tornado.web.Application(
    web_handlers + api_handlers +
    [
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"})
    ],
    debug=True,
    cookie_secret="dev@yummy",
    xsrf_cookies=True,
    login_url='/login',
    template_path='templates',
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
