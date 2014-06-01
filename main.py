import re
import tornado.ioloop
import tornado.web
import html2text
import logging
import functools
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from tornado.auth import GoogleOAuth2Mixin
from readability.readability import Document
from elasticsearch import Elasticsearch
from search import index, search
from charlockholmes import detect


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
        logging.exception('extract html')
        return {}


def html_to_text(html):
    clean_html = html2text.HTML2Text()
    clean_html.ignore_links = True
    clean_html.ignore_images = True

    return clean_html.handle(html)


@gen.coroutine
def get_and_extract(url, timeout=5):
    http_client = AsyncHTTPClient()
    try:
        resp = yield http_client.fetch(url, connect_timeout=timeout)
    except:
        logging.exception('fetch: %s' % url)
        raise gen.Return({})
    info = detect(resp.body)
    body = resp.body.decode(info['encoding'], errors='ignore')

    raise gen.Return(extract(body))


def logined(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kw):
        if not self.current_user:
            self.redirect("/login")
        return func(self, *args, **kw)
    return wrapper


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return tornado.escape.xhtml_escape(self.get_secure_cookie("user") or '')


class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")


class GoogleOAuthHandler(BaseHandler, GoogleOAuth2Mixin):
    @gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            code = self.get_argument('code')
            print code
            user = yield self.get_authenticated_user(
                redirect_uri='http://www.allsunday.in:8888/auth/google',
                code=code)
            print user
            # self.set_secure_cookie("user", self.get_argument("name"))
        else:
            yield self.authorize_redirect(
                redirect_uri='http://www.allsunday.in:8888/auth/google',
                client_id=self.settings['google_oauth']['key'],
                scope=['openid', 'profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


class MainHandler(BaseHandler):
    @logined
    def get(self):
        user = self.current_user
        self.write("Hello, " + user)


class ExtractHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        url = self.get_argument('url', '')
        inform = yield get_and_extract(url)
        if not inform:
            self.finish('error')
            raise gen.Return()

        self.finish(
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
        user = self.current_user
        bookmark_file = self.request.files.get('bookmark')[0]
        body = bookmark_file.body
        matches = HREF_REGEXP.finditer(body)
        for m in matches:
            url = m.group(1)
            self.write('processing %s<br>' % url)
            self.flush()
            inform = yield get_and_extract(url)
            if not inform:
                continue
            self.write('<p>title: %s</p>' % inform.get('title'))
            index(url, inform['title'], inform['article'], inform['full_text'], user)


class SearchHandler(BaseHandler):
    @logined
    def get(self):
        user = self.current_user
        query = self.get_argument('query', '')
        if query:
            offset = int(self.get_argument('offset', 0))
            limit = int(self.get_argument("limit", 30))
            links = search(query, offset, limit, user)
            self.render("templates/search.html", query=query, links=links, offset=offset, limit=limit)
        else:
            self.render("templates/search.html", query="")


class AddBookmarkHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        url = self.get_argument('url')
        inform = yield get_and_extract(url)
        if not inform:
            self.finish('error')

        title = inform['title']
        article = inform['article']
        index(url, title, article, self.current_user)


application = tornado.web.Application([
    (r"/", SearchHandler),
    (r"/extract", ExtractHandler),
    (r'/import', ImportBookmarksHandler),
    (r"/login", LoginHandler),
    (r"/search", SearchHandler),
    (r"/add", AddBookmarkHandler),
    (r"/auth/google", GoogleOAuthHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"})
],
    debug=True,
    autoreload=True,
    cookie_secret="dev@yummy",
    google_oauth={
        'key': '546860121082-ud7ps1vt57badn28vs83vojv6v7qor2n.apps.googleusercontent.com',
        'secret': '76aBh8MbikO61E7kaAKfSroC',
    }
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
