#coding:utf8
from datetime import datetime
from elasticsearch import Elasticsearch


# by default we connect to localhost:9200
es = Elasticsearch()

INDEX = 'testindex'
DOC_TYPE = 'testtype'


def index(id, title, article, user="tizac"):
    es.index(
        index=INDEX,
        doc_type=DOC_TYPE,
        id=id,
        body={
            "user": user,
            "title": title,
            "article": article,
            "timestamp": datetime.now()
        }
    )


def search(query, offset=0, limit=10, user="tizac"):
    if user:
        body = {
                'query': {
                    'filtered': {
                        'query': {
                            "query_string": {
                                "query": query
                            }
                        },
                        'filter': {
                            "term": {
                                "user": user
                            }
                        }
                    }
                }
            }
    else:
        body = {
            'query': {
                'filtered': {
                    'query': {
                        "query_string": {
                            "query": query
                        }
                    }
                }
            }
        }

    result = es.search(
        index=INDEX,
        doc_type=DOC_TYPE,
        from_=offset,
        size=limit,
        body=body
    )
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
