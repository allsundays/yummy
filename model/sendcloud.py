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
        body = render_mail_body("/auth/activate.html", data)
        self.send_mail(to_mail=user.ua.mail, title='欢迎注册下厨房，请验证您的邮箱', body=body)

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


if __name__ == '__main__':
    to_mails = [
        "tizzac@gmail.com"
    ]
    test_send_cloud(to_mails)
