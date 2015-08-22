import os
import webapp2
import jinja2

from webapp2_extras import routes
from basehandler import basehandler
from wikiengine import odb_handlers

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

PAGE_RE = r'([0-9]{4}-[0-9]{2}-[0-9]{2})'

app = webapp2.WSGIApplication([
            ('/admin/tasks/odb', odb_handlers.FetchOdb),
            ('/admin/odb/?', odb_handlers.OdbHome),
            ('/admin/odb/?' + PAGE_RE, odb_handlers.OdbToday),
            ('/admin/odb/_delete/?' + PAGE_RE, odb_handlers.DeleteOdb),
            ], debug=DEBUG)
