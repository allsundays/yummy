import re
import tornado.ioloop
import tornado.web
import html2text
import functools
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from readability.readability import Document
from elasticsearch import Elasticsearch
from search import index, search


HREF_REGEXP = re.compile(r'href=["\'](.*?)[\'"]', re.IGNORECASE)
es = Elasticsearch()


def extract(html):
    try:
        doc = Document(html)
        article = doc.summary()
        title = doc.short_title()
        return {
            'title': title,
            'article': html_to_text(article),
            'full_text': html_to_text(html)
        }
    except:
        return {}


def html_to_text(html):
    clean_html = html2text.HTML2Text()
    clean_html.ignore_links = True
    clean_html.ignore_images = True

    return clean_html.handle(html)


def logined(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kw):
        if not self.current_user:
            self.redirect("/login")
        return func(self, *args, **kw)
    return wrapper


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
    @logined
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        self.write("Hello, " + user)


class ExtractHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        url = self.get_argument('url', '')
        http_client = AsyncHTTPClient()
        resp = yield http_client.fetch(url)
        body = resp.body.decode('utf8')

        inform = extract(body)
        if not inform:
            self.finish('error')
            raise gen.Return()

        self.write(
            u'''
            <p>{title}</p>
            <p>{article}</p>
            '''.format(**inform)
        )


class ImportBookmarksHandler(BaseHandler):
    @logined
    def get(self):
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
                self.write('fetch %s error<br>' % url)
                continue
            inform = extract(resp.body)
            if not inform:
                continue
            self.write('<p>title: %s</p>' % inform.get('title'))
            index(url, inform['title'], inform['article'], inform['full_text'], user)


class SearchHandler(BaseHandler):
    @logined
    def get(self):
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
