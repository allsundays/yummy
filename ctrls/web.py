# coding:utf8
import re
import urlparse
import datetime
from tornado import gen
from tornado.web import authenticated, HTTPError, RequestHandler, RedirectHandler
from models.bookmark import Bookmark
from models.user import User
from utils.extract import get_and_extract


HREF_REGEXP = re.compile(r'href=["\'](.*?)[\'"]', re.IGNORECASE)


def login(req, user):
    req.set_secure_cookie('mail', user.mail)


def logout(req):
    req.clear_all_cookies()


class BaseHandler(RequestHandler):
    def get_template_namespace(self):
        namespace = super(BaseHandler, self).get_template_namespace()
        namespace.update({
            'query': '',
            'url_for': self.reverse_url,
            'dformat': lambda d, f: d.strftime(f),
        })
        return namespace


class LoginRequiredMixin(object):
    @authenticated
    def prepare(self):
        pass

    def get_current_user(self):
        return User.get(self.get_secure_cookie("mail"))


class RegisterHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
        self.render('register.html', error='')

    def post(self):
        mail = self.get_argument('mail')
        password1 = self.get_argument('password1')
        password2 = self.get_argument('password2')

        if User.get(mail):
            error = 'user exist'
        elif not mail.strip():
            error = 'mail can not be empty'
        elif not password1.strip() or not password2.strip():
            error = 'password can not be empty'
        elif password1 != password2:
            error = 'passwords do not match'
        else:
            u = User.create(mail, password1)
            if u:
                login(self, u)
                return self.redirect('/')

        self.render('register.html', error=error)


class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
        self.render('login.html', error='')

    def post(self):
        mail = self.get_argument('mail')
        password = self.get_argument('password')

        if not mail.strip():
            error = 'mail can not be empty'
        elif not password.strip():
            error = 'password can not be empty'
        elif not User.verify(mail, password):
            error = 'mail and password do not match'
        else:
            u = User.get(mail)
            login(self, u)

            return self.redirect('/')

        self.render('login.html', error=error)


class LogoutHandler(LoginRequiredMixin, BaseHandler):
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


class ImportBookmarksHandler(LoginRequiredMixin, BaseHandler):
    def get(self):
        return self.render('import_bookmarks.html')

    @gen.coroutine
    def post(self):
        bookmark_file = self.request.files.get('bookmark')[0]
        body = bookmark_file.body
        matches = HREF_REGEXP.finditer(body)
        user = self.current_user

        for m in matches:
            url = m.group(1)
            self.write('processing %s<br>' % url)
            self.flush()
            inform = yield get_and_extract(url)
            if not inform:
                continue
            self.write('<p>title: %s</p>' % inform.get('title'))
            Bookmark.create(user, url, inform['title'], inform['article'], inform['full_text'])


class ExportBookmarksHandler(LoginRequiredMixin, BaseHandler):
    def get(self):
        now = datetime.datetime.now()
        self.set_header('Content-type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename="yummy-bookmarks-%s.html"' % now.strftime("%Y-%m-%d_%H:%M:%S"))
        user = self.current_user
        links = Bookmark.latest_in_user(user, offset=0, limit=100000)
        self.render("export_bookmarks.html", links=links)


class SearchHandler(LoginRequiredMixin, BaseHandler):
    def get(self):
        query = self.get_argument('query', '')
        offset = int(self.get_argument('offset', 0))
        limit = int(self.get_argument("limit", 30))
        search_path = self.reverse_url('search')
        user = self.current_user
        if query:
            links = Bookmark.search_in_user(user, query, offset, limit)
        else:
            links = Bookmark.latest_in_user(user, offset, limit)
        next_page_url = u'{search_path}?query={query}&offset={offset}&limit={limit}'.format(
            search_path=search_path, query=query, offset=offset+limit, limit=limit)

        self.render("search.html",
            query=query, next_page_url=next_page_url, links=links,
            favicon_url=self.favicon_url)

    def favicon_url(self, url):
        o = urlparse.urlparse(url)
        return '%s://%s/favicon.ico' % (o.scheme, o.netloc)


class AddBookmarkHandler(LoginRequiredMixin, BaseHandler):
    @gen.coroutine
    def post(self):
        url = self.get_argument('url')
        inform = yield get_and_extract(url)
        if not inform:
            raise HTTPError(500, 'processing url error')

        user = self.current_user
        title = inform['title']
        article = inform['article']
        full_text = inform['full_text']
        Bookmark.create(user, url, title, article, full_text)


web_handlers = [
    (r"/", RedirectHandler, {'url': '/search'}, 'index'),
    (r"/extract", ExtractHandler, {}, 'extract'),
    (r'/import', ImportBookmarksHandler, {}, 'import'),
    (r'/export', ExportBookmarksHandler, {}, 'export'),
    (r"/register", RegisterHandler, {}, 'register'),
    (r"/login", LoginHandler, {}, 'login'),
    (r"/logout", LogoutHandler, {}, 'logout'),
    (r"/search", SearchHandler, {}, 'search'),
    (r"/add", AddBookmarkHandler, {}, 'add'),
]
