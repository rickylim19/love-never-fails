#! /usr/bin/env python
# -*- coding: utf-8 -*-

from basehandler import basehandler
import re
from google.appengine.api import search
from datetime import datetime
from libs.models.quotemodels import *
from libs.models.todomodels import *
from libs.models.odbmodels import *
import config
import urllib
from google.appengine.api import memcache

class AdminHome(basehandler.BaseHandler):
    """
    Handles the admin view page /admin/admin_home.html
    - The admin home has the search feature for searching text in all wikis published
    """
    def get(self):
        self.render('admin/admin_home.html')

    def post(self):
        query = self.request.get('search').strip()
        if query:
            # sort results by date descending
            expr_list = [search.SortExpression(
                expression='date', default_value=datetime(1999, 01, 01),
                direction=search.SortExpression.DESCENDING)]
            # construct the sort options
            sort_opts = search.SortOptions(
                expressions=expr_list)
            query_options = search.QueryOptions(
                limit = 10,
                snippeted_fields=['content'],
                sort_options=sort_opts,
                returned_fields = ['path_link'])

            query_obj = search.Query(query_string=query, options=query_options)
            results = search.Index(name = config.__INDEX_NAME__).search(query=query_obj)
            len_results = len(results.results)

            self.render('admin/admin_home.html', results = results,
                        len_results = len_results, query = query)

class AddQuote(basehandler.BaseHandler):
    """
    Handles the addition of quotes to be displayed in the home jumbotron
    """
    def get(self):
        if self.useradmin:
            self.render("admin/admin_addQuote.html")

    def post(self):
        if self.useradmin:
            quote = self.request.get('content')
            source = self.request.get('source')
            uname = self.useradmin.nickname()

            if quote:
                # put quote into datastore and added to memcache
                Quote._add_quote(quote = quote,
                            source = source,
                            username = uname)
                #self.render('thankyou.html', name = uname)
                self.redirect('/admin/home/quote')
            else:
                error = "Add a quote please!"
                self.render("admin/admin_addQuote.html", error=error)

class AddWiki(basehandler.BaseHandler):
    """
    Add wiki path
    """
    def get(self):
        self.render('admin/admin_addWiki.html')

    def post(self):
        if self.useradmin:

            path = str(self.request.get('path'))
            path = urllib.quote(path.encode('utf-8'))
            #path = path.replace(' ', '_')
            internal = str(self.request.get('internal'))
            PAGE_RE = r'^[a-zA-Z0-9-_?%]+$'
            if re.match(PAGE_RE, path):
                if internal:
                    path = '/admin/_edit/internal/%s' % (path)
                else:
                    path = '/admin/_edit/%s' % (path)
                self.redirect(path)
            else:
                error = "Oops, we could not create a wiki for <b>'%s\n'</b>  \
                         Please check your wiki name and try again." %(path)
                self.render("admin/admin_addWiki.html", error = error)

class AddTodo(basehandler.BaseHandler):
    """
    Add a list to TODO list
    """
    def get(self):
        self.render('admin/admin_addTodo.html')

    def post(self):
        if self.useradmin:
            title = self.request.get('title')
            description = self.request.get('description')
            priority = self.request.get('priority')
            if priority != '': priority = int(priority)
            else: priority = 3
            due = self.request.get('due')
            if due:
                due = datetime.strptime(due, "%Y-%m-%d").date()
                if due < datetime.now().date():
                    error = 'Due date was in the passed!'
                    self.render("admin/admin_addTodo.html", error=error)
            else: due = None
            if title:
                # put quote into datastore and added to memcache
                todo_items = {
                    'title': title,
                    'description': description,
                    'priority': priority,
                    'due': due,
                    }
                Todo._add_todo(**todo_items)
                self.redirect('/admin/home/todo')
            else:
                error = "Add a todo please!"
                self.render("admin/admin_addTodo.html", error=error)

class TodoHandler(basehandler.BaseHandler):
    """
    Handles the todo list
    """
    def get(self):
        todos = Todo._get_all()
        if todos:
            self.render('admin/admin_todo.html', todos = todos)
        else:
            message = 'Nothing to get done yet!'
            self.render('admin/admin_todo.html', message = message)

    def post(self):
        if self.useradmin:
            title = self.request.get('title')
            description = self.request.get('description')
            priority = int(self.request.get('priority'))
            due = datetime.strptime(self.request.get('due'), "%Y-%m-%d").date()
            if title:
                todo_items = {
                    'title': title,
                    'description': description,
                    'priority': priority,
                    'due': due,
                }
                Todo._add_todo(**todo_items)
                self.render('thankyou.html')
            else:
                error = "Add a title please!"
                self.render("admin/admin_addQuote.html", error=error)

class EditTodo(basehandler.BaseHandler):
    def get(self, id):
        if id:
            id = id.replace('/', '')
            todo = Todo._by_id(int(id))
            self.render('admin/admin_addTodo.html', todo = todo)
        else:
            self.handle_error(404)

    def post(self, id):
        if id:
            id = id.replace('/', '')
            title = self.request.get('title')
            description = self.request.get('description')
            priority = int(self.request.get('priority'))
            due = self.request.get('due')
            if due:
                due = datetime.strptime(due, "%Y-%m-%d").date()
            else:
                due = None
            if title:
                todo = Todo._by_id(int(id))
                todo_items = {
                    'title': title,
                    'description': description,
                    'priority': priority,
                    'due': due,
                    }
                todo._update_todo(**todo_items)
                self.redirect('/admin/home/todo')
            else:
                error = "Add a title for Todo please"
                self.render("admin/admin_addTodo.html", error=error)
        else:
            self.handle_error(404)

class TodoCheck(basehandler.BaseHandler):
    """
    Handles the check and uncheck of the todo
    - checked todo: completed will be set to True and stricken when displayed
    """
    def get(self, id):
        if id:
            completed = True
            if self.isUncheck(id):
                completed = False
                id = id.replace('uncheck/', '')
            id = id.replace('/', '')
            todo = Todo._by_id(int(id))
            todo.completed = completed
            todo.put()
            self.redirect('/admin/home/todo')
        else:
            self.handle_error(404)

class TodoDelete(basehandler.BaseHandler):
    def get(self, id):
        if id:
            id = id.replace('/', '')
            todo = Todo._by_id(int(id))
            ndb.delete_multi([todo.key])
            self.redirect('/admin/home/todo')
        else:
            self.handle_error(404)

class QuoteHandler(basehandler.BaseHandler):
    def get(self):
        quotes = Quote._get_all()
        self.render('/admin/admin_quote.html', quotes = quotes)

class EditQuote(basehandler.BaseHandler):
    def get(self, quote_id):
        quote = Quote.get_by_id(int(quote_id))
        logging.error(quote)
        self.render("/admin/edit_quote.html", quote_id = quote_id, q = quote)
    def post(self, quote_id):

        content = self.request.get('content')
        source = self.request.get('source')
        q = Quote.get_by_id(int(quote_id))
        if content :
            if (content != q.quote) or (source != q.source):
                q.quote = content
                q.source = source
                q.put()
            self.redirect("/admin/home/")
        else:
            error = "Add a quote please!"
            self.render("/admin/edit_quote.html", quote_id = quote_id, error=error)

class DeleteQuote(basehandler.BaseHandler):
    def get(self, quote_id):
        if self.useradmin:
            quote = Quote.get_by_id(int(quote_id))
            quote.key.delete()
        self.redirect("/admin/home/quote")

