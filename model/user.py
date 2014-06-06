#coding:utf8
import hashlib
from model.base import Model, NotFoundError
from config import SALT


class UserExistException(Exception):
    pass


class User(Model):
    class Meta:
        doc_type = 'user'

    def __init__(self, mail, password):
        self.mail = mail
        self.password = password

    def __str__(self):
        return u'<User: %s>' % self.mail

    @classmethod
    def create(cls, mail, password):
        if cls.get(mail):
            raise UserExistException('User %s exists' % mail)

        hashed_passwd = hash_with_salt(password)
        cls._index(
            id=mail,
            body={
                'password': hashed_passwd
            }
        )
        return cls(mail, hashed_passwd)

    @classmethod
    def get(cls, mail):
        try:
            doc = cls._get(id=mail)
            return cls(mail, doc['_source']['password'])
        except NotFoundError:
            return

    @classmethod
    def verify(cls, mail, password):
        u = cls.get(mail)
        return hash_with_salt(password) == u.password


def hash_with_salt(s):
    return hashlib.sha512(s + SALT).hexdigest()


def test():
    pass


if __name__ == "__main__":
    test()
