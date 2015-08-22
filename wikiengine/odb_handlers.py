#! /usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
#from datetime import datetime
import datetime
import addlib
from bs4 import BeautifulSoup
from basehandler import basehandler
from libs.models.odbmodels import *
from google.appengine.api import urlfetch
import logging
import urllib
from libs.utils.markdown2 import *
from bs4 import BeautifulSoup
from google.appengine.api import search


def CreateDocument(path, path_link, content) :
    return search.Document(
        doc_id = path,
        fields = [search.TextField(name = 'path', value = path),
                  search.TextField(name = 'path_link', value = path_link),
                  search.HtmlField(name = 'content', value = content),
                  #search.DateField(name = 'date', value = datetime.now().date())])
                  search.DateField(name = 'date', value = datetime.datetime.now().date())])

# format 2015/02/25
urlfetch.set_default_fetch_deadline(60)

def getHtml(url):
    #response = urllib2.urlopen(url).read()
    response = urlfetch.fetch(url).content
    return response

def getToday():
    """
    return date of today, e.g: "2015/02/24"
    note that the datetime.now was in UTC zone
    """
    #today = datetime.strftime(datetime.now(), "%Y-%m-%d")

    # add 1 day to be for the next day
    today = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days = 1),
                                       "%Y-%m-%d")
    return today


def fetchOdb(odb_date = getToday()):

    """
    param: today date (e.g"2015/02/24")
    fetch from http://mobi.rbc.org.odb
    """

    # open the archive of the odb
    odb_url = 'http://mobi.rbc.org/odb/' + odb_date + '.html'
    html_content = getHtml(odb_url)
    content = BeautifulSoup(html_content)
    odb_title =  content.find("div", "headtop")
    odb_passage = content.find(id = "article-passage")
    odb_verse = content.find(id = "article-verse")
    odb_content = content.find(id = "article-content")
    odb_poem = content.find(id = "article-poem")
    odb_insight= content.find(id = "article-thought")


    return (odb_title, odb_verse, odb_passage, odb_content, odb_poem, odb_insight)

class FetchOdb(basehandler.BaseHandler):
    def get(self):
        try:
            TODAY = getToday()
            (odb_title, odb_verse, odb_passage, odb_content, odb_poem, odb_insight) = fetchOdb(TODAY)
            path = TODAY.replace('/', '-')
            path_link = 'admin/odb/' + path
            o = OdbPage(parent = OdbPage._parent_key(path),
                        path = str(path),
                        title = str(odb_title),
                        verse = str(odb_verse),
                        passage = str(odb_passage),
                        content = str(odb_content),
                        poem = str(odb_poem),
                        insight = str(odb_insight))
            o.put()

            # add into search index document
            raw_content = "%s %s %s %s %s %s" %(odb_title, odb_verse, odb_passage,
                                                odb_content, odb_poem, odb_insight)

            raw_soup = BeautifulSoup(raw_content)
            raw_content = raw_soup.get_text()
            search.Index(name = 'odb').put(CreateDocument(path = path,
                                                          path_link = path_link,
                                                          content = raw_content))

        except:
            logging.warn("can't fetch")
            return



class OdbHome(basehandler.BaseHandler):
    """
    Show the devotionals for the last 4 days
    """
    def get(self):
        all_pages = True if self.request.get('all') == 'True' else False
        pages = OdbPage._get_n_odb() if all_pages else OdbPage._get_n_odb(4)
        page_content = []

        for page in pages:
            if page is not None:
                (path, title, content) = page.path, page.title, page.content
                page_content.append((path, title, content))

        self.render('odbhome.html', pages = page_content)

    def post(self):
        query = self.request.get('search').strip()
        if query:
            # sort results by date descending
            expr_list = [search.SortExpression(
                expression='date', default_value=datetime.datetime(1999, 01, 01),
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
            results = search.Index(name = 'odb').search(query=query_obj)
            len_results = len(results.results)

            self.render('odbhome.html', results = results,
                        len_results = len_results, query = query)

class OdbToday(basehandler.BaseHandler):
    def get(self, path):
        edit = self.request.get('edit') and True or False
        odb_page = OdbPage._by_path(path).get()
        logging.error(edit)

        if odb_page:
            odb_title = odb_page.title
            odb_verse = odb_page.verse
            odb_passage = odb_page.passage
            odb_content = odb_page.content
            odb_poem = odb_page.poem
            odb_insight = odb_page.insight
        else:
            (odb_title, odb_verse, odb_passage, odb_content, odb_poem, odb_insight) = fetchOdb(path)
            o = OdbPage(parent = OdbPage._parent_key(path),
                        path = str(path),
                        title = str(odb_title),
                        verse = str(odb_verse),
                        passage = str(odb_passage),
                        content = str(odb_content),
                        poem = str(odb_poem),
                        insight = str(odb_insight))
            o.put()

        odb_note = odb_page and odb_page.note or None
        if not edit and odb_note: odb_note =  markdown(odb_note)
        self.render('odb.html', edit = edit, odb_note = odb_note,
                    path = path,
                    title = odb_title,
                    verse = odb_verse,
                    passage = odb_passage,
                    content = odb_content,
                    poem = odb_poem,
                    insight = odb_insight)
    def post(self, path):
        odb_note = self.request.get('content')
        if odb_note:
            odb_page = OdbPage._by_path(path).get()
            if odb_page:
                odb_page.note = odb_note
                odb_page.put()
                odb_note = odb_page.note
                odb_title = odb_page.title
                odb_verse = odb_page.verse
                odb_passage = odb_page.passage
                odb_content = odb_page.content
                odb_poem = odb_page.poem
                odb_insight = odb_page.insight

                raw_content = "%s %s %s %s %s %s %s" %(odb_title, odb_verse, odb_passage,
                                                       odb_content, odb_poem, odb_insight,
                                                       odb_note)
                raw_soup = BeautifulSoup(raw_content)
                raw_content = raw_soup.get_text()
                path_link = '/admin/odb/' + path
                search.Index(name = 'odb').put(CreateDocument(path = path,
                                                              path_link = path_link,
                                                              content = raw_content))
            self.redirect(path)

class DeleteOdb(basehandler.BaseHandler):
    """
    Handles odb deletion given its path
    and delete the document index as well (given the docID which the path)
    Note: document index is used for full-text search
    """
    def get(self, path):
        path = urllib.quote(path.encode('utf-8'))

        if self.useradmin:
            key_ = OdbPage.query(OdbPage.path == path).fetch(keys_only = True)
            ndb.delete_multi(key_)


            # delete the document index
            doc_index = search.Index(name = 'odb')
            doc_index.delete(path)
            self.redirect('/admin/odb/')

