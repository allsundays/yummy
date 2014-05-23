import tornado.ioloop
import tornado.web
import re
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from readability.readability import Document


HREF_REGEXP = re.compile(r'href=["\'](.*?)[\'"]', re.IGNORECASE)


def extract(text):
    try:
        doc = Document(text)
        article = doc.summary()
        title = doc.short_title()
        return title, article
    except:
        return None, None


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Hello, world!')


class ExtractHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        url = self.get_argument('url', '')
        http_client = AsyncHTTPClient()
        resp = yield http_client.fetch(url)
        title, article = extract(resp.body)
        self.write(title)
        self.write(article)


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
                self.write('fetch %s error' % url)
                continue
            title, article = extract(resp.body)
            self.write('<p>title: %s</p>' % title)
            self.flush()


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/extract", ExtractHandler),
    (r'/import', ImportBookmarksHandler),
],
    debug=True,
    autoreload=True,
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
