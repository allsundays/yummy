#!/usr/bin/env python
#coding:utf8
import requests
from config import SYS_MAIL_SENDER, SYS_MAIL_SENDER_NAME, SEND_CLOUD_CONFIG


class SendCloud(object):
    '''
    封装了send cloud服务，用web api方式发送邮件
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


mailsender = SendCloud(
    default_from_name=SYS_MAIL_SENDER_NAME,
    default_from_mail=SYS_MAIL_SENDER,
    **SEND_CLOUD_CONFIG
)


def test():
    to_mail = "tizzac@gmail.com"
    mailsender.send_mail(to_mail=to_mail, title="test sendcloud", body="test sendcloud")


if __name__ == '__main__':
    test()
