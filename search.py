#coding:utf8
from datetime import datetime
from elasticsearch import Elasticsearch


# by default we connect to localhost:9200
es = Elasticsearch()

INDEX = 'testindex'
DOC_TYPE = 'testtype'


def index(id, content, user):
    es.index(
        index=INDEX,
        doc_type=DOC_TYPE,
        id=id,
        body={
            "content": content,
            "user": user,
            "timestamp": datetime.now()
        }
    )


def search(query, user):
    result = es.search(
        index=INDEX,
        doc_type=DOC_TYPE,
        body={
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
    rst = search("桂鱼")
    for x in rst:
        print x['_score'], x['_source']["content"]


if __name__ == "__main__":
    # test_index()
    test_search()
