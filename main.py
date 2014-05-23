import tornado.ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from readability.readability import Document


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Hello, world!')


class ExtractHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        url = self.get_argument('url', '')
        http_client = AsyncHTTPClient()
        resp = yield http_client.fetch(url)
        title, article = self.extract(resp.body)
        self.write(title)
        self.write(article)

    def extract(self, text):
        doc = Document(text)
        article = doc.summary()
        title = doc.short_title()
        return title, article


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/extract", ExtractHandler),
],
    debug=True,
    autoreload=True,
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
