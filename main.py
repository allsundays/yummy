import re
import tornado.ioloop
import html2text
import logging
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from tornado.web import authenticated, HTTPError, RedirectHandler, RequestHandler
from readability.readability import Document
from elasticsearch import Elasticsearch
from model.search import index, search
from charlockholmes import detect
from model.user import User


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


def login(req, user):
    req.set_secure_cookie('mail', user.mail)


def logout(req):
    req.clear_all_cookies()


class BaseHandler(RequestHandler):
    def get_current_user(self):
        return User.get(self.get_secure_cookie("mail"))

    def get_template_namespace(self):
        namespace = super(BaseHandler, self).get_template_namespace()
        namespace.update({
            'query': ''
        })
        return namespace


class LoginRequiredMixin(RequestHandler):
    @authenticated
    def prepare(self):
        pass


class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
        self.render('templates/login.html')

    def post(self):
        mail = self.get_argument('mail')
        password = self.get_argument('password')

        if User.verify(mail, password):
            u = User.get(mail)
            login(self, u)

            return self.redirect('/')

        self.render('templates/login.html', error='Invalid mail or password')


class LogoutHandler(BaseHandler, LoginRequiredMixin):
    def get(self):
        logout(self)
        self.redirect(self.settings.get('login_url'))


class ExtractHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        url = self.get_argument('url', '')
        inform = yield get_and_extract(url)
        if not inform:
            raise HTTPError(500, 'error')

        self.finish(
            u'''
            <p>{title}</p>
            <p>{article}</p>
            '''.format(**inform)
        )


class ImportBookmarksHandler(BaseHandler, LoginRequiredMixin):
    def get(self):
        return self.render('templates/import_bookmarks.html',
            user=self.current_user, query='', avatar=self.avatar)

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


class SearchHandler(BaseHandler, LoginRequiredMixin):
    def get(self):
        query = self.get_argument('query', '')
        offset = int(self.get_argument('offset', 0))
        limit = int(self.get_argument("limit", 30))
        search_path = self.reverse_url('search')
        links = search(query, offset, limit, self.current_user)
        next_page_url = u'{search_path}?query={query}&offset={offset}&limit={limit}'.format(
            search_path=search_path, query=query, offset=offset+limit, limit=limit)

        self.render("templates/search.html",
            query=query, next_page_url=next_page_url, links=links)


class AddBookmarkHandler(BaseHandler, LoginRequiredMixin):
    @gen.coroutine
    def post(self):
        url = self.get_argument('url')
        inform = yield get_and_extract(url)
        if not inform:
            raise HTTPError(500, 'processing url error')

        title = inform['title']
        article = inform['article']
        index(url, title, article, inform['full_text'], self.current_user)


application = tornado.web.Application([
    (r"/", RedirectHandler, {'url': '/search'}),
    (r"/extract", ExtractHandler),
    (r'/import', ImportBookmarksHandler),
    (r"/login", LoginHandler),
    (r"/logout", LogoutHandler),
    (r"/search", SearchHandler, {}, 'search'),
    (r"/add", AddBookmarkHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"})
],
    debug=True,
    autoreload=True,
    cookie_secret="dev@yummy",
    xsrf_cookies=True,
    login_url='/login',
    google_oauth={
        'key': '546860121082-ud7ps1vt57badn28vs83vojv6v7qor2n.apps.googleusercontent.com',
        'secret': '76aBh8MbikO61E7kaAKfSroC',
    }
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
