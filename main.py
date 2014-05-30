import tornado.ioloop
import tornado.web
import re
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from readability.readability import Document
from datetime import datetime
from elasticsearch import Elasticsearch
from search import index, search


HREF_REGEXP = re.compile(r'href=["\'](.*?)[\'"]', re.IGNORECASE)
es = Elasticsearch()


def extract(text):
    try:
        doc = Document(text)
        article = doc.summary()
        title = doc.short_title()
        return title, article
    except:
        return None, None


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.write("Hello, " + name)


class ExtractHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        url = self.get_argument('url', '')
        http_client = AsyncHTTPClient()
        resp = yield http_client.fetch(url)
        title, article = extract(resp.body)
        self.write(title)
        self.write(article)


class ImportBookmarksHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        return self.render('templates/import_bookmarks.html')

    @gen.coroutine
    def post(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        bookmark_file = self.request.files.get('bookmark')[0]
        body = bookmark_file.body
        matches = HREF_REGEXP.finditer(body)
        for m in matches:
            url = m.group(1)
            self.write('processing %s<br>' % url)
            self.flush()
            try:
                resp = yield AsyncHTTPClient().fetch(url, connect_timeout=5)
            except:
                self.write('fetch %s error' % url)
                continue
            title, article = extract(resp.body)
            self.write('<p>title: %s</p>' % title)
            index(url, title, article, user)
            self.flush()


class SearchHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        user = tornado.escape.xhtml_escape(self.current_user)
        query = self.get_argument('query', '')
        if query:
            offset = int(self.get_argument('offset', 0))
            limit = int(self.get_argument("limit", 30))
            links = search(query, offset, limit, user)
            self.render("templates/search.html", query=query, links=links, offset=offset, limit=limit)
        else:
            self.render("templates/search.html", query="")


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/extract", ExtractHandler),
    (r'/import', ImportBookmarksHandler),
    (r"/login", LoginHandler),
    (r"/search", SearchHandler),
],
    debug=True,
    autoreload=True,
    cookie_secret="dev@yummy"
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
