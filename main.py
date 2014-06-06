import re
import md5
import tornado.ioloop
import html2text
import logging
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from tornado.auth import GoogleOAuth2Mixin
from tornado.web import authenticated, HTTPError, RedirectHandler, RequestHandler
from readability.readability import Document
from elasticsearch import Elasticsearch
from search import index, search
from charlockholmes import detect
from lib.google_user_id_token import parse_id_token

HREF_REGEXP = re.compile(r'href=["\'](.*?)[\'"]', re.IGNORECASE)
GRAVATAR = 'http://www.gravatar.com/avatar/%s?s=40'
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


def login(req, user, access_token=None):
    email = user
    user_name = email.split('@')[0]
    avatar = GRAVATAR % md5.new(email.lower()).hexdigest()
    req.set_secure_cookie('user', user_name)
    req.set_secure_cookie('email', email)
    req.set_secure_cookie('avatar', avatar)
    if access_token:
        req.set_secure_cookie('access_token', access_token)


def logout(req):
    req.clear_all_cookies()


class BaseHandler(RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class LoginRequiredMixin(RequestHandler):
    @authenticated
    def prepare(self):
        super(LoginRequiredMixin, self).prepare()
        self.email = self.get_secure_cookie('email')
        self.avatar = self.get_secure_cookie('avatar')


class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
        self.render('templates/login.html')


class LogoutHandler(BaseHandler, LoginRequiredMixin):
    def get(self):
        logout(self)
        self.redirect(self.settings.get('login_url'))


class GoogleOAuthHandler(BaseHandler, GoogleOAuth2Mixin):
    @gen.coroutine
    def get(self):
        code = self.get_argument('code', False)
        if code:
            info = yield self.exchange_code_for_access_token(code)
            self._save_info(info)
            self.redirect(self.get_argument('next', '/'))
        else:
            yield self.request_for_code()

    def exchange_code_for_access_token(self, code):
        if self.get_argument('state', '') != self.xsrf_token:
            raise HTTPError(403, "state does not match")

        return self.get_authenticated_user(
            redirect_uri='http://www.allsunday.in:8888/auth/google',
            code=code)

    def request_for_code(self):
        return self.authorize_redirect(
            redirect_uri='http://www.allsunday.in:8888/auth/google',
            client_id=self.settings['google_oauth']['key'],
            scope=['openid', 'profile', 'email'],
            response_type='code',
            extra_params={'approval_prompt': 'auto', 'state': self.xsrf_token})

    def _save_info(self, info):
        access_token = info['access_token']
        id_token = parse_id_token(info['id_token'])
        email = id_token['email']
        login(self, email, access_token)


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
        next_page_url = search_path = self.reverse_url('search')
        links = []
        if query:
            links = search(query, offset, limit, self.current_user)
            next_page_url = u'{search_path}?query={query}&offset={offset}&limit={limit}'.format(
                search_path=search_path, query=query, offset=offset+limit, limit=limit)

        self.render("templates/search.html",
            query=query, next_page_url=next_page_url, links=links,
            user=self.current_user, avatar=self.avatar)


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
    (r"/auth/google", GoogleOAuthHandler),
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
