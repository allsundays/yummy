#coding: utf8
from elasticsearch import Elasticsearch, NotFoundError # noqa
from config import INDEX

es = Elasticsearch()


_models = []


class _Meta:
    index = INDEX
    doc_type = None


class MetaModel(type):
    def __new__(cls, name, bases, attrs):
        clazz = super(MetaModel, cls).__new__(cls, name, bases, attrs)

        if not getattr(clazz, 'es', None):
            clazz.es = es

        Meta = getattr(clazz, 'Meta', None)
        if not Meta:
            clazz.Meta = _Meta
        elif not getattr(Meta, 'index', None):
            Meta.index = _Meta.index

        if name != 'Model':
            _models.append(clazz)

        return clazz


class Model(object):
    __metaclass__ = MetaModel

    @classmethod
    def _index(cls, *args, **kwargs):
        return cls.es.index(
            *args,
            index=cls.Meta.index,
            doc_type=cls.Meta.doc_type,
            **kwargs
        )

    @classmethod
    def _get(cls, *args, **kwargs):
        return es.get(
            *args,
            index=cls.Meta.index,
            doc_type=cls.Meta.doc_type,
            **kwargs
        )
