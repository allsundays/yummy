#coding:utf8
import hashlib
import datetime
from models.base import Model, NotFoundError
from config import SALT, DOMAIN
from utils.sendcloud import mailsender


GRAVATAR = 'http://www.gravatar.com/avatar/%s?s=40'


class UserExistException(Exception):
    pass


class User(Model):
    class Meta:
        doc_type = 'user'

    def __init__(self, mail, password, status, avatar=None):
        self.id = self.gen_id(mail)
        self.mail = mail
        self.password = password
        self.status = status
        self.avatar = GRAVATAR % hashlib.md5(mail.lower()).hexdigest()

    def __str__(self):
        return u'<User: %s>' % self.mail

    @classmethod
    def create(cls, mail, password, status="init"):
        id = cls.gen_id(mail)
        if cls.get(id):
            raise UserExistException('User %s exists' % mail)

        hashed_passwd = hash_with_salt(password)
        cls._index(
            id=id,
            body={
                'mail': mail,
                'password': hashed_passwd,
                'status': status
            }
        )
        return cls(mail, hashed_passwd, status)

    @classmethod
    def get(cls, id):
        try:
            doc = cls._get(id=id)
            return cls(doc['_source']['mail'], doc['_source']['password'], doc['_source']['status'])
        except NotFoundError:
            return

    @classmethod
    def get_by_mail(cls, mail):
        if not mail:
            return
        id = cls.gen_id(mail)
        return cls.get(id)

    @classmethod
    def verify(cls, mail, password):
        id = cls.gen_id(mail)
        u = cls.get(id)
        return u and hash_with_salt(password) == u.password

    @classmethod
    def gen_id(cls, mail):
        return hashlib.sha512(mail.lower()).hexdigest()

    @property
    def session(self):
        # fixme 回头做个严格的session
        key = self.id + str(datetime.date.today())
        return hash_with_salt(key)

    def save(self):
        self._index(
            id=self.id,
            body={
                'mail': self.mail,
                'password': self.password,
                'status': self.status
            }
        )

    def activate(self):
        self.status = "active"
        self.save()

    def reset_password(self, password):
        self.password = hash_with_salt(password)
        self.save()

    def send_activate_mail(self):
        body = '''
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
            <title>欢迎注册yummy，请验证你的邮箱</title>
          </head>
          <body style='padding:10px;'>
            <div style='margin-bottom:20px;'>用户你好：</div>
            <div style='margin:5px 0px 5px 0px;'>你刚才在yummy申请注册了，因此我们发送这封邮件进行确认。</div>
            <div style='margin:5px 0px 5px 0px;'>请在七天内点击下面的链接来验证您的邮箱。</div>
            <div style='margin:5px 0px 5px 0px;'><a href='http://{domain}/user/activate?uid={user_id}&session={session}'>
                http://{domain}/user/activate?uid={user_id}&session={session}
                </a></div>
            <div style='margin:5px 0px 5px 0px;'>如果无法点击上面的链接，可以复制该地址，并粘帖在浏览器的地址栏中访问。</div>
          </body>
        </html>
        '''.format(user_id=self.id, domain=DOMAIN, session=self.session)
        mailsender.send_mail(to_mail=self.mail, title='欢迎注册yummy，请验证你的邮箱', body=body)

    def send_reset_password_mail(self):
        body = '''
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
            <title>yummy重置密码邮件</title>
          </head>
          <body style='padding:10px;'>
            <div style='margin-bottom:20px;'> 你好：</div>
            <div style='margin:5px 0px 5px 0px;'>你刚才在 {domain} 申请了找回密码。</div>
            <div style='margin:5px 0px 5px 0px;'>请点击下面的链接来重置密码：</div>
            <div style='margin:5px 0px 5px 0px;'><a href='http://{domain}/user/resetpassword?uid={user_id}&session={session}'>
            http://{domain}/user/resetpassword?uid={user_id}&session={session}</a></div>
            <div style='margin:5px 0px 5px 0px;'>如果无法点击上面的链接，可以复制该地址，并粘帖在浏览器的地址栏中访问。</div>
          </body>
        </html>
        '''.format(user_id=self.id, domain=DOMAIN, session=self.session)
        mailsender.send_mail(to_mail=self.mail, title='yummy重置密码邮件', body=body)


def hash_with_salt(s):
    return hashlib.sha512(s + SALT).hexdigest()


def test():
    u = User.get_by_mail("tizzac@gmail.com")
    u.send_reset_password_mail()


if __name__ == "__main__":
    test()
