#!/usr/bin/env python
#coding:utf8
import requests


class SendCloud(object):
    '''
    封装了第三方的send cloud服务，用web api方式发送邮件
    官方提供的例子见http://sendcloud.sohu.com/sendcloud/api-doc/web-api-python-examples
    '''

    def __init__(self, url, api_user, api_key, default_from_name, default_from_mail):
        self.url = url
        self.api_user = api_user
        self.api_key = api_key
        self.default_from_name = default_from_name
        self.default_from_mail = default_from_mail

    def send_mail(self, to_mail, title, body, from_mail=None, from_name=None, files={}):
        from_mail = from_mail or self.default_from_mail
        from_name = from_name or self.default_from_name
        params = {
            "api_user": self.api_user,
            "api_key": self.api_key,
            "to": to_mail,
            "from": from_mail,
            "fromname": from_name,
            "subject": title,
            "html": body
        }
        r = requests.post(self.url, files=files, data=params)
        return r.text

    def send_activate_mail(self, user):
        data = {
            "recipient_name": user.name,
            "domain": DOMAIN,
            "ck": user.ck,
            "uid": user.id
        }

        body = '''
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
            <title>欢迎注册下厨房，请验证您的邮箱</title>
          </head>
          <body style='padding:10px;'>
            <div style='margin-bottom:20px;'>用户您好：</div>
            <div style='margin:5px 0px 5px 0px;'>“<b>${recipient_name}</b>”刚才在下厨房申请注册了，因此我们发送这封邮件进行确认。</div>
            <div style='margin:5px 0px 5px 0px;'>请在七天内点击下面的链接来验证您的邮箱。</div>
            <div style='margin:5px 0px 5px 0px;'><a href='http://${domain}/auth/active/${uid}/${ck}/'>http://${domain}/auth/active/${uid}/${ck}/</a></div>
            <div style='margin:5px 0px 5px 0px;'>如果无法点击上面的链接，您可以复制该地址，并粘帖在浏览器的地址栏中访问。</div>
          </body>
        </html>
        '''
        body = render_mail_body("/auth/activate.html", data)
        self.send_mail(to_mail=user.mail, title='欢迎注册yummy，请验证你的邮箱', body=body)

    def send_reset_password_mail(self, user):
        data = {
            "recipient_name": user.name,
            "domain": DOMAIN,
            "rand_key": user.session()
        }
        body = render_mail_body("/auth/reset_password.html", data)
        self.send_mail(to_mail=user.ua.mail, title='下厨房重置密码邮件', body=body)


SEND_CLOUD_CONFIG = dict(
    url="https://sendcloud.sohu.com/webapi/mail.send.xml",
    api_user="postmaster@info2.xiachufang.com",
    api_key="4Czw7fir"
)

SYS_EMAIL_SENDER = "noreply@xiachufang.com"
SYS_EMAIL_SENDER_NAME = "测试"

def test_send_cloud(to_mails):
    send_cloud = SendCloud(
        default_from_name=SYS_EMAIL_SENDER_NAME,
        default_from_mail=SYS_EMAIL_SENDER,
        **SEND_CLOUD_CONFIG
    )
    for to_mail in to_mails:
        send_cloud.send_mail(to_mail=to_mail, title="test sendcloud", body="test sendcloud")


def test():
    body = '''
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
            <title>欢迎注册下厨房，请验证您的邮箱</title>
          </head>
          <body style='padding:10px;'>
            <div style='margin-bottom:20px;'>用户您好：</div>
            <div style='margin:5px 0px 5px 0px;'><b>${user_name}</b>刚才在下厨房申请注册了，因此我们发送这封邮件进行确认。</div>
            <div style='margin:5px 0px 5px 0px;'>请在七天内点击下面的链接来验证您的邮箱。</div>
            <div style='margin:5px 0px 5px 0px;'><a href='http://${domain}/auth/active/${uid}/${ck}/'>http://${domain}/auth/active/${uid}/${ck}/</a></div>
            <div style='margin:5px 0px 5px 0px;'>如果无法点击上面的链接，您可以复制该地址，并粘帖在浏览器的地址栏中访问。</div>
          </body>
        </html>
    '''.format(user_name="tizac", domain="www.xiachufang.com", uid=1, ck=3)
    print body


if __name__ == '__main__':
    to_mails = [
        "tizzac@gmail.com"
    ]
    # test_send_cloud(to_mails)
    test()
