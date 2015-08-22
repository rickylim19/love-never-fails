#! /usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
import random
from google.appengine.api import memcache
import logging
from basehandler import basehandler

class Quote(ndb.Model):
    """
    Datastore for quotes
    """
    quote = ndb.TextProperty(required=True)
    source = ndb.StringProperty()
    username = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def _get_all(cls):
        quotes = list(Quote.query().order(-cls.created).fetch(limit = None))
        return quotes

    # Save a quote and return it
    @classmethod
    def _add_quote(cls, **kwargs):
        quote = cls(quote = kwargs['quote'],
                    source = kwargs['source'],
                    username = kwargs['username'],
                   )
        quote.put()
        return quote


    def _as_dict(self):
        time_fmt = '%c'
        d = {'quote': self.quote,
             'source': self.source,
             'username': self.username,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.created.strftime(time_fmt)}
        return d
