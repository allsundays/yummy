import tornado.ioloop
from tornado.web import RedirectHandler

from ctrls.web import RegisterHandler, LoginHandler, LogoutHandler, ExtractHandler, ImportBookmarksHandler, SearchHandler, AddBookmarkHandler


application = tornado.web.Application([
    (r"/", RedirectHandler, {'url': '/search'}, 'index'),
    (r"/extract", ExtractHandler, {}, 'extract'),
    (r'/import', ImportBookmarksHandler, {}, 'import'),
    (r"/register", RegisterHandler, {}, 'register'),
    (r"/login", LoginHandler, {}, 'login'),
    (r"/logout", LogoutHandler, {}, 'logout'),
    (r"/search", SearchHandler, {}, 'search'),
    (r"/add", AddBookmarkHandler, {}, 'add'),
    (r"/explore", ExploreHandler, {}, 'explore'),
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
