#coding:utf8
from datetime import datetime
from elasticsearch import Elasticsearch


# by default we connect to localhost:9200
es = Elasticsearch()

INDEX = 'yummy_dev'
DOC_TYPE = 'link'


def index(url, title, article, full_text, user):
    id = "%s:%s" % (user, url)
    es.index(
        index=INDEX,
        doc_type=DOC_TYPE,
        id=id,
        body={
            "url": url,
            "user": user,
            "title": title,
            "article": article,
            "full_text": full_text,
            "timestamp": datetime.now()
        }
    )


def search(query, offset=0, limit=10, user=None):
    if user:
        if query:
            body = {
                    'query': {
                        'filtered': {

                            "query": {
                                "bool": {
                                    "must": {
                                        "match": {
                                            "full_text": {
                                                "query":    query,
                                                "operator": "and"
                                            }
                                        }
                                    },
                                    "should": [
                                        { "match": {
                                            "title": {
                                                "query": query,
                                                "boost": 10
                                            }
                                        }},
                                        { "match": {
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
                                    "user": user
                                }
                            }
                        }
                    },
                    "highlight": {
                        "fields": {
                            "title": {},
                            "full_text": {"fragment_size" : 40}
                        }
                    },
                }
        else:
            body = {
                    'query': {
                        'filtered': {
                            'query': {
                                "match_all" : { }
                            },
                            'filter': {
                                "term": {
                                    "user": user
                                }
                            }
                        }
                    },
                    'sort': [
                          {"timestamp" : {"order" : "desc"}}
                       ]
                }
    else:
        if query:
            body = {
                "query": {
                    "bool": {
                        "must": {
                            "match": {
                                "full_text": {
                                    "query":    query,
                                    "operator": "and"
                                }
                            }
                        },
                        "should": [
                            { "match": {
                                "title": {
                                    "query": query,
                                    "boost": 10
                                }
                            }},
                            { "match": {
                                "article": {
                                    "query": query,
                                    "boost": 3
                                }
                            }}
                        ]
                    },
                }
            }
        else:
            body = {
                    'query': {
                        'filtered': {
                            'query': {
                                "match_all" : { }
                            }
                        }
                    },
                    'sort': [
                          {"timestamp" : {"order" : "desc"}}
                       ]
                }
    try:
        result = es.search(
            index=INDEX,
            doc_type=DOC_TYPE,
            from_=offset,
            size=limit,
            body=body
        )
    except:
        return []
    # for link in result['hits']['hits']:
    #     if 'highlight' in link:
    #         print link['highlight']
    #         print "########"
    return result['hits']['hits']


def test_index():
    f = file("/tmp/recipe_names")
    id = 0
    for name in f.readlines():
        id += 1
        name = name.strip()
        index(id, name)


def test_search():
    rst = search("桂鱼", user=None)
    for x in rst:
        print x


if __name__ == "__main__":
    # test_index()
    test_search()
