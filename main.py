#!/usr/bin/env python

import webapp2
import jinja2
import os
import logging
import random
from google.appengine.ext import ndb
from google.appengine.api import users

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')

class LoginHandler(webapp2.RequestHandler):
  def get(self):
    loginurl = users.create_login_url(dest_url='/', _auth_domain=None, federated_identity=None)
    self.redirect(loginurl)
class LogoutHandler(webapp2.RequestHandler):
  def get(self):
    dest_url = '/'
    logouturl = users.create_logout_url(dest_url)
    self.redirect(logouturl)
    logging.info(logouturl)

jinja_environment = jinja2.Environment(loader=
      jinja2.FileSystemLoader(os.path.dirname(__file__)))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/Logout', LogoutHandler),
    ('/Login', LoginHandler),
    ('/wallet', WalletHandler),
    ('/makePaper', PaperHandler),
    ('/colophon', ColophonHandler),
    ('/theory', TheoryHandler),
    ('/settings', SettingsHandler),
], debug=True)

