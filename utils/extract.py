import logging
import html2text
import re
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


charset_regexp = re.compile(r'charset=(.*?)\s?$', re.IGNORECASE)


@gen.coroutine
def get_and_extract(url, timeout=5):
    http_client = AsyncHTTPClient()
    try:
        resp = yield http_client.fetch(url, connect_timeout=timeout)
    except:
        logging.exception('fetch: %s' % url)
        raise gen.Return({})

    content_type = resp.headers.get('Content-Type')
    segs = charset_regexp.findall(content_type)
    if segs:
        charset = segs[0]
    else:
        charset = detect(resp.body).get('encoding', '')

    try:
        body = resp.body.decode(charset, errors='ignore')
    except LookupError:
        body = resp.body.decode('utf8', errors='ignore')

    raise gen.Return(extract(body))
