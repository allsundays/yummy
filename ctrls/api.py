#coding: utf8
from tornado import gen
from tornado.web import authenticated
from lib.api_handler import APIHandler, APIError
from models.user import User
from itsdangerous import URLSafeSerializer, BadSignature
from config import SECRET_KEY
from utils.extract import get_and_extract
from models.bookmark import Bookmark


serializer = URLSafeSerializer(SECRET_KEY)


class LoginRequiredMixin(object):
    @authenticated
    def prepare(self):
        pass

    def get_current_user(self):
        sk = self.get_argument('sk', '')
        try:
            email = serializer.loads(sk)
        except BadSignature:
            raise APIError(401)
        return User.get(email)


class LoginHandler(APIHandler):
    def post(self):
        mail = self.get_argument('mail').strip()
        password = self.get_argument('password').strip()

        print mail, password
        if not User.verify(mail, password):
            raise APIError(401, 'mail and password doesn\'t match.')

        return self.success(serializer.dumps(mail))


class AddBookmarkHandler(LoginRequiredMixin, APIHandler):
    @gen.coroutine
    def post(self):
        url = self.get_argument('url')
        inform = yield get_and_extract(url)
        if not inform:
            raise APIError(500, 'processing url error')

        user = self.current_user
        title = inform['title']
        article = inform['article']
        full_text = inform['full_text']
        Bookmark.create(user, url, title, article, full_text)


api_handlers = [
    (r'/api/v1/login', LoginHandler),
    (r'/api/v1/add', AddBookmarkHandler),
]
