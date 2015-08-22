#! /usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
from google.appengine.api import memcache
import logging

class Todo(ndb.Model):
    """
    Datastore for todo list
    """
    title = ndb.StringProperty(required = True)
    description = ndb.TextProperty()
    priority = ndb.IntegerProperty(default = 1)
    due = ndb.DateProperty()
    completed = ndb.BooleanProperty(default = False)
    created = ndb.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def _parent_key(names = 'todos'):
        return ndb.Key('/root/', names)

    @classmethod
    def _by_id(cls, page_id):
        return cls.get_by_id(page_id, cls._parent_key())

    @classmethod
    def _get_all(cls):
        todos = list(Todo.query().order(-cls.created).fetch(limit = None))
        return todos

    @classmethod
    def _add_todo(cls, **kwargs):
        todo = cls(parent = cls._parent_key(), **kwargs)
        todo.put()
        return todo

    def _update_todo(self, **kwargs):
        todo = Todo(key = self.key, **kwargs)
        todo.put()
        return todo

