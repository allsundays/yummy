import re
from tornado import gen
from tornado.web import authenticated, HTTPError, RequestHandler
from models.bookmark import Bookmark
from models.user import User

from utils.extract import get_and_extract


HREF_REGEXP = re.compile(r'href=["\'](.*?)[\'"]', re.IGNORECASE)


def login(req, user):
    req.set_secure_cookie('mail', user.mail)


def logout(req):
    req.clear_all_cookies()


class BaseHandler(RequestHandler):
    def get_current_user(self):
        u = User.get_by_mail(self.get_secure_cookie("mail"))
        if u and u.status == u"active":
            return u
        return None

    def get_template_namespace(self):
        namespace = super(BaseHandler, self).get_template_namespace()
        namespace.update({
            'query': '',
            'url_for': self.reverse_url,
        })
        return namespace


class LoginRequiredMixin(RequestHandler):
    @authenticated
    def prepare(self):
        pass


class RegisterHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
        self.render('register.html', error='')

    def post(self):
        mail = self.get_argument('mail')
        password1 = self.get_argument('password1')
        password2 = self.get_argument('password2')

        if User.get_by_mail(mail):
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
                u.send_activate_mail()
                self.write("please check your mail")
        if error:
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
            u = User.get_by_mail(mail)
            if u and u.status == u"active":
                login(self, u)
                return self.redirect('/')
            else:
                error = "user not active, please check your mail"

        self.render('login.html', error=error)


class LogoutHandler(BaseHandler, LoginRequiredMixin):
    def get(self):
        logout(self)
        self.redirect(self.settings.get('login_url'))


class UserActivateHandler(BaseHandler):
    def get(self):
        uid = self.get_argument('uid')
        session = self.get_argument('session')
        u = User.get(uid)
        if u.session == session:
            u.activate()
            self.write('<p>activation success!</p>')
            self.write("<a href='/login'>click here to login</a>")
        else:
            self.write("activation fail!")


class RetrievePasswordHandler(BaseHandler):
    def get(self):
        self.render("retrieve_password.html")

    def post(self):
        mail = self.get_argument("mail")
        print mail
        user = User.get_by_mail(mail)
        if user:
            user.send_reset_password_mail(mail)
            self.write("check your mail box")
        else:
            self.write("User not exist")


class ResetPasswordHandler(BaseHandler):
    def get(self):
        uid = self.get_argument('uid')
        session = self.get_argument('session')
        u = User.get(uid)
        print u
        if session and u and u.session == session:
            self.render('reset_password.html', error='')
        else:
            self.write("authenticated fail")

    def post(self):
        uid = self.get_argument('uid')
        password1 = self.get_argument('password1')
        password2 = self.get_argument('password2')

        u = User.get(uid)
        if not u:
            error = 'uid error'
        elif not password1.strip() or not password2.strip():
            error = 'password can not be empty'
        elif password1 != password2:
            error = 'passwords do not match'
        else:
            u.reset_password(password1)
            login(self, u)
            return self.redirect('/')

        self.render('reset_password.html', error=error)


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


class SearchHandler(BaseHandler, LoginRequiredMixin):
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
                    query=query, next_page_url=next_page_url, links=links)


class AddBookmarkHandler(BaseHandler, LoginRequiredMixin):
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
