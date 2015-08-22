#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2

from webapp2_extras import routes
from wikiengine import wiki_handlers
from users import users_handlers
from basehandler import basehandler
from adminhandler import admin_handlers

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# page dir that is allowed only for alphabets, numbers, '-', and '_' only
#PAGE_RE = r'(/(?:[a-zA-Z0-9-_?]+/?)*)'
ID_RE = r'(/(?:[a-zA-Z0-9]+/?)*)'
PAGE_RE = r'(.*)'
app = webapp2.WSGIApplication([
         ('/admin/home/?', admin_handlers.AdminHome),
         ('/admin/home/addTodo', admin_handlers.AddTodo),
         ('/admin/home/addQuote', admin_handlers.AddQuote),
         ('/admin/home/addWiki', admin_handlers.AddWiki),
         ('/admin/home/todo', admin_handlers.TodoHandler),
         ('/admin/home/quote', admin_handlers.QuoteHandler),
         ('/admin/_edit/quote/'+ PAGE_RE, admin_handlers.EditQuote),
         ('/admin/_delete/quote/'+ PAGE_RE, admin_handlers.DeleteQuote),
         ('/admin/todocheck' + PAGE_RE, admin_handlers.TodoCheck),
         ('/admin/tododelete' + PAGE_RE, admin_handlers.TodoDelete),
         ('/admin/_edit/todo' + PAGE_RE, admin_handlers.EditTodo),
         ('/admin/internal/pages.json', wiki_handlers.InternalPageJson),
         ('/admin/internal/?', wiki_handlers.InternalHome),
         ('/admin/_delete' + PAGE_RE, wiki_handlers.DeletePage),
         ('/admin/signup', users_handlers.Signup),
         ('/admin/addquote', admin_handlers.AddQuote),
         ('/admin/_edit' + PAGE_RE, wiki_handlers.EditPage),
         ('/admin/_history' + PAGE_RE, wiki_handlers.HistoryPage),
         ('/admin' + PAGE_RE, wiki_handlers.WikiPage),
         ('/.*', basehandler.NotFound),
         ], debug=DEBUG)


