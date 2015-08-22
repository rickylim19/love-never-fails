#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import jinja2
import webapp2
import cgi
import hmac
import json
from libs.utils.utils import *
#from libs.models.usermodels import *
#from libs.models.pagemodels import *
#from libs.models.quotemodels import *
from google.appengine.api import users
from google.appengine.api import memcache
from datetime import datetime, timedelta
from google.appengine.api import images
import urllib
import urllib2
import addlib
from bs4 import BeautifulSoup
from google.appengine.api import urlfetch

def datetimeformat(value, format='%Y-%m-%d'):
    if value != None and value != '':
        return value.strftime(format)

def pathformat(value, format='%Y-%m-%d'):
    if value != None and value != '':
        return urllib.unquote(value.encode('ascii').decode('utf-8'))

def day2go(value):
    if value:
        days = value - datetime.now().date()
        return days.days


jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(['templates/', 'templates/admin']),
                               autoescape=True)

jinja_env.filters['datetimeformat'] = datetimeformat
jinja_env.filters['day2go'] = day2go
jinja_env.filters['pathformat'] = pathformat


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        params['admin'] = self.useradmin
        params['admin_logout'] = users.create_logout_url('/')
        params['uname'] = self.uname # for admin nickname
        t = jinja_env.get_template(template)
        return t.render(params)

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
                'Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))
    
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    # check user_id cookie for every request (every instance creation)
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User._by_id(int(uid))
        self.useradmin = users.is_current_user_admin() and users.get_current_user()
        if self.useradmin:
            self.uname = users.get_current_user().nickname().split('@')[0]
        else:
            self.uname = None
        #if self.user: self.uname = self.user.name
        #self.useradmin = users.get_current_user()
        #self.isadmin = users.is_current_user_admin()

        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'

    def isInternal(self, path):
        """
        returns True if path == '/admin/internal'
        """
        dir_name = os.path.dirname(path)
        if dir_name == '/internal':
            return True
        else: return False

    def isUncheck(self, path):
        """
        returns True if path =='/admin/todocheck/uncheck'
        """
        dir_name = os.path.dirname(path)
        if dir_name == '/uncheck':
            return True
        else: return False

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header(
                'Set-Cookie', 'user_id=; Path=/')

    def handle_error(self, code):

        # Log the error.
        #logging.exception(code)

        page_title = 'Ohh Snap, An Error has Occured!!'
        super(BaseHandler, self).error(code) #override the error method
        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if code == 403:
            message = 'Sorry Your request can not be completed!'
        elif code == 404:
            message = 'Oops! This wiki has no resource to handle your request'
        elif code == 'nonadmin':
            message = 'Oops! for admin only'

        else:
            message = 'A server error occurred!'

        self.render('error.html',
                    page_title = page_title,
                    message = message)

    def next_url(self):
        self.request.headers.get('referer', '/')


class NotFound(BaseHandler):
    """
    Handles unexpected requests
    """
    def get(self):
        self.handle_error(404)

def rescale(img_data, width, height, halign='middle', valign='middle'):
  """Resize then optionally crop a given image.

  Attributes:
    img_data: The image data
    width: The desired width
    height: The desired height
    halign: Acts like photoshop's 'Canvas Size' function, horizontally
            aligning the crop to left, middle or right
    valign: Verticallly aligns the crop to top, middle or bottom

  """
  image = images.Image(img_data)
  image.im_feeling_lucky()

  desired_wh_ratio = float(width) / float(height)
  wh_ratio = float(image.width) / float(image.height)

  if desired_wh_ratio > wh_ratio:
    # resize to width, then crop to height
    image.resize(width=width)
    image.execute_transforms()
    trim_y = (float(image.height - height) / 2) / image.height
    if valign == 'top':
      image.crop(0.0, 0.0, 1.0, 1 - (2 * trim_y))
    elif valign == 'bottom':
      image.crop(0.0, (2 * trim_y), 1.0, 1.0)
    else:
      image.crop(0.0, trim_y, 1.0, 1 - trim_y)
  else:
    # resize to height, then crop to width
    image.resize(height=height)
    image.execute_transforms()
    trim_x = (float(image.width - width) / 2) / image.width
    if halign == 'left':
      image.crop(0.0, 0.0, 1 - (2 * trim_x), 1.0)
    elif halign == 'right':
      image.crop((2 * trim_x), 0.0, 1.0, 1.0)
    else:
      image.crop(trim_x, 0.0, 1 - trim_x, 1.0)


  return image.execute_transforms()


