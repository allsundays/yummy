#coding:utf8
import hashlib
from models.base import Model, NotFoundError
from config import SALT


GRAVATAR = 'http://www.gravatar.com/avatar/%s?s=40'


class UserExistException(Exception):
    pass


class User(Model):
    class Meta:
        doc_type = 'user'

    def __init__(self, mail, password, avatar=None):
        self.id = self.gen_id(mail)
        self.mail = mail
        self.password = password
        self.avatar = GRAVATAR % hashlib.md5(mail.lower()).hexdigest()

    def __str__(self):
        return u'<User: %s>' % self.mail

    @classmethod
    def create(cls, mail, password):
        id = cls.gen_id(mail)
        if cls.get(id):
            raise UserExistException('User %s exists' % mail)

        hashed_passwd = hash_with_salt(password)
        cls._index(
            id=id,
            body={
                'password': hashed_passwd
            }
        )
        return cls(mail, hashed_passwd)

    @classmethod
    def get(cls, mail):
        if not mail:
            return
        try:
            id = cls.gen_id(mail)
            doc = cls._get(id=id)
            return cls(mail, doc['_source']['password'])
        except NotFoundError:
            return

    @classmethod
    def verify(cls, mail, password):
        id = cls.gen_id(mail)
        u = cls.get(id)
        return u and hash_with_salt(password) == u.password

    @classmethod
    def gen_id(cls, mail):
        return hashlib.sha512(mail.lower()).hexdigest()


def hash_with_salt(s):
    return hashlib.sha512(s + SALT).hexdigest()


def test():
    pass


if __name__ == "__main__":
    test()
