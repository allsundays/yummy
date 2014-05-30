import re
import tornado.ioloop
import tornado.web
import html2text
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from readability.readability import Document
from elasticsearch import Elasticsearch
from search import index, search


HREF_REGEXP = re.compile(r'href=["\'](.*?)[\'"]', re.IGNORECASE)
es = Elasticsearch()


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
        return {}


def html_to_text(html):
    clean_html = html2text.HTML2Text()
    clean_html.ignore_links = True
    clean_html.ignore_images = True

    return clean_html.handle(html)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Hello, world!')


class ExtractHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        url = self.get_argument('url', '')
        http_client = AsyncHTTPClient()
        resp = yield http_client.fetch(url)
        body = resp.body.decode('utf8')

        inform = extract(body)
        if not inform:
            return self.finish('error')

        self.write(
            u'''
            <p>{title}</p>
            <p>{article}</p>
            '''.format(**inform)
        )


class ImportBookmarksHandler(tornado.web.RequestHandler):
    def get(self):
        return self.render('templates/import_bookmarks.html')

    @gen.coroutine
    def post(self):
        bookmark_file = self.request.files.get('bookmark')[0]
        body = bookmark_file.body
        matches = HREF_REGEXP.finditer(body)
        for m in matches:
            url = m.group(1)
            self.write('processing %s<br>' % url)
            self.flush()
            try:
                resp = yield AsyncHTTPClient().fetch(url, connect_timeout=5)
            except:
                self.write('fetch %s error<br>' % url)
                continue
            inform = extract(resp.body)
            if not inform:
                continue
            title = inform['title']
            article = inform['article']
            self.write('<p>title: %s</p>' % inform.get('title'))
            index(url, title, article)


class SearchHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_argument('user', 'tizac')
        query = self.get_argument('query', '')
        result = search(query, user)
        for x in result:
            self.write(x['_source']["title"])
            self.write('<br>')


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/extract", ExtractHandler),
    (r'/import', ImportBookmarksHandler),
    (r"/search", SearchHandler),
],
    debug=True,
    autoreload=True,
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
