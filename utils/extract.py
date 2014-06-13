import logging
import html2text
from charlockholmes import detect
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from readability.readability import Document


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
