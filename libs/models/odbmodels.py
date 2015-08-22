#! /usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

class OdbPage(ndb.Model):
    path = ndb.StringProperty(required=True)
    username = ndb.StringProperty()
    title = ndb.TextProperty()
    verse = ndb.TextProperty()
    passage = ndb.TextProperty()
    content = ndb.TextProperty(required=True)
    poem = ndb.TextProperty()
    insight = ndb.TextProperty()
    note = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)

    @staticmethod
    def _parent_key(path):
        return ndb.Key('/root/' + path, 'odbpages')

    @classmethod
    def _by_path(cls, path):
        q = cls.query(ancestor = cls._parent_key(path))
        return q

    @classmethod
    def _get_four(cls):
        #p = list(OdbPage.query().fetch(limit = None))
        p = OdbPage.query().order(-cls.created)
        p = list(p.fetch(4))
        return p

    @classmethod
    def _get_n_odb(cls, n = None):
        o = OdbPage.query().order(-cls.created)
        o = list(o.fetch(limit=n))
        return o
