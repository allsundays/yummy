#coding:utf8
from elasticsearch import Elasticsearch


# by default we connect to localhost:9200
es = Elasticsearch()

INDEX = 'testindex'
DOC_TYPE = 'user'


def index(mail, password):
    es.index(
        index=INDEX,
        doc_type=DOC_TYPE,
        id=mail,
        body={
            "mail": mail,
            "password": password
        }
    )


def get(mail):
    es.get(
        index=INDEX,
        doc_type=DOC_TYPE,
        id=mail
    )


def test():
    pass


if __name__ == "__main__":
    test()
