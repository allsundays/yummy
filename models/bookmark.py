#coding:utf8
import hashlib
from datetime import datetime
from models.base import Model, NotFoundError


class Bookmark(Model):
    class Meta:
        doc_type = 'bookmark'

    def __init__(self, user, url, title, article, full_text):
        self.user = user
        self.url = url
        self.title = title
        self.article = article
        self.full_text = full_text
        self.timestamp = datetime.now()

    def __str__(self):
        return u'<Bookmark: %s>' % self.url

    @property
    def id(self):
        key = "%s:%s" % (self.user.mail, self.url)
        return hashlib.sha512(key).hexdigest()

    @classmethod
    def create(cls, user, url, title, article, full_text):
        bookmark = cls(user, url, title, article, full_text)
        # print bookmark.id
        cls._index(
            id=bookmark.id,
            body={
                "url": bookmark.url,
                "user_mail": bookmark.user.hashed_mail,
                "title": bookmark.title,
                "article": bookmark.article,
                "full_text": bookmark.full_text,
                "timestamp": bookmark.timestamp
            }
        )
        # print cls._get(id=bookmark.id)
        return bookmark

    @classmethod
    def get(cls, id):
        try:
            doc = cls._get(id=id)
            return doc
        except NotFoundError:
            return

    @classmethod
    def latest_in_user(cls, user, offset=0, limit=10):
        try:
            body = {
                'query': {
                    'filtered': {
                        'query': {
                            "match_all": {}
                        },
                        'filter': {
                            "term": {
                                "user_mail": user.hashed_mail
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
        except:
            return []
        return ret

    @classmethod
    def search_in_user(cls, user, query, offset=0, limit=10):
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
                            "user_mail": user.hashed_mail
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
    # Bookmark.create(
    #     user_mail="tizzac@gmail.com",
    #     url="http://www.xiachufang.com/",
    #     title="title test",
    #     article="article test",
    #     full_text="full_text test"
    # )
    from model.user import User
    u = User.get("tizzac1@gmail.com")
    print Bookmark.get('tizzac1@gmail.com:http://www.baidu.com')
    print Bookmark.search_in_user(u, '百度')
    print "*****************"
    for link in Bookmark.search_in_site("百度", limit=5):
        print link['_id']
    # print Bookmark.latest_in_site(limit=1)


if __name__ == "__main__":
    # test_index()
    # test_search()
    test()
