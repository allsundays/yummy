#coding:utf8
from datetime import datetime
from model.base import Model


class Bookmark(Model):
    class Meta:
        doc_type = 'bookmark'

    def __init__(self, user_mail, url, title, article, full_text):
        self.url = url
        self.user_mail = user_mail
        self.url = url
        self.title = title
        self.article = article
        self.full_text = full_text
        self.timestamp = datetime.now()

    def __str__(self):
        return u'<Bookmark: %s>' % self.url

    @property
    def id(self):
        return "%s:%s" % (self.user_mail, self.url)

    @classmethod
    def create(cls, user_mail, url, title, article, full_text):
        bookmark = cls(user_mail, url, title, article, full_text)
        # print bookmark.id
        cls._index(
            id=bookmark.id,
            body={
                "url": bookmark.url,
                "user_mail": bookmark.user_mail,
                "title": bookmark.title,
                "article": bookmark.article,
                "full_text": bookmark.full_text,
                "timestamp": bookmark.timestamp
            }
        )
        # print cls._get(id=bookmark.id)
        return bookmark

    @classmethod
    def latest_in_user(cls, user_mail, offset=0, limit=10):
        body = {
            'query': {
                'filtered': {
                    'query': {
                        "match_all": {}
                    },
                    'filter': {
                        "term": {
                            "user_mail": user_mail
                        }
                    }
                }
            },
            'sort': [
                {"timestamp": {"order": "desc"}}
            ]
        }
        ret = cls._search(
            from_=offset,
            size=limit,
            body=body
            )
        return ret

    @classmethod
    def search_in_user(cls, user_mail, query, offset=0, limit=10):
        body = {
            'query': {
                'filtered': {
                    "query": {
                        "bool": {
                            "should": [
                                {"match": {
                                    "full_text": {
                                        "query": query,
                                    }
                                }},
                                {"match": {
                                    "title": {
                                        "query": query,
                                        "boost": 10
                                    }
                                }},
                                {"match": {
                                    "article": {
                                        "query": query,
                                        "boost": 3
                                    }
                                }}
                            ]
                        },
                    },

                    'filter': {
                        "term": {
                            "user_mail": user_mail
                        }
                    }
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "full_text": {"fragment_size": 40}
                }
            },
        }

        ret = cls._search(
            from_=offset,
            size=limit,
            body=body
            )
        return ret

    @classmethod
    def latest_in_site(cls, offset=0, limit=10):
        body = {
            'query': {
                'filtered': {
                    'query': {
                        "match_all": {}
                    }
                }
            },
            'sort': [
                {"timestamp": {"order": "desc"}}
            ]
        }
        ret = cls._search(
            from_=offset,
            size=limit,
            body=body
            )
        return ret

    @classmethod
    def search_in_site(cls, query, offset=0, limit=10):
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {
                            "full_text": {
                                "query": query,
                            }
                        }},
                        {"match": {
                            "title": {
                                "query": query,
                                "boost": 10
                            }
                        }},
                        {"match": {
                            "article": {
                                "query": query,
                                "boost": 3
                            }
                        }}
                    ]
                },
            }
        }
        ret = cls._search(
            from_=offset,
            size=limit,
            body=body
            )
        return ret


def test():
    Bookmark.create(
        user_mail="tizzac",
        url="http://www.xiachufang.com/",
        title="title test",
        article="article test",
        full_text="full_text test"
    )
    print Bookmark.search_in_user('tizzac', "title")
    # print Bookmark.search_in_site("title")


if __name__ == "__main__":
    # test_index()
    # test_search()
    test()
