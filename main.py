# -*- coding: utf-8 -*-

"""
Online translation for camptocamp.org
"""

import cgi
import logging
import os
import models
import utils
from mako.template import Template
from mako.lookup import TemplateLookup
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

###############################################################

def get_greeting():
  user = users.get_current_user()
  if user:
    greeting = ('%s | <a class="loggedin" href="%s">Sign out</a>' %
      (user.nickname(), cgi.escape(users.create_logout_url('/'))))
  else:
    greeting = ('<a  href=\"%s\">Sign in</a>' %
      cgi.escape(users.create_login_url("/")))
  return greeting

###############################################################

def error404(req):
  req.response.set_status(404, 'Page not Found')

  template_file = os.path.join(os.path.dirname(__file__), 'templates/404.html')
  template_values = {
    'greeting': get_greeting(),
     'is_admin': users.is_current_user_admin(),
  }

  req.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

###############################################################

def edit_filter_suffix(lang_filter, state_filter):
  suffix = ''

  if not lang_filter is None:
    suffix += '/filter/lang/' + lang_filter
  elif not state_filter is None:
    suffix += '/filter/lang/all'

  if not state_filter is None:
    suffix += '/' + state_filter

  return suffix

###############################################################

def secure_page(handler, need_admin=False):
  user = users.get_current_user()
  admin = users.is_current_user_admin()
  if not user or (not admin and need_admin):
    handler.redirect(users.create_login_url(handler.request.uri))

##############################################################

def retrieve_charts():
  values = []
  for status in models.STATUSES:
    status_values = []
    for lang in models.LANGS:
      lang_counters = models.Counter.all().filter('lang =', lang).get()
      if lang_counters is None:
        return None
      status_values.append(int(getattr(lang_counters, status)))
    values.append(status_values)

  return values

###############################################################

def chart_url(chart_values):
  values = []

  if chart_values is None:
    return ""

  for status_values in chart_values:
    values.append(",".join(map(str, status_values)))
  values_string = "|".join(values)

  total = chart_values[0][0] + chart_values[1][0] + chart_values[2][0] + chart_values[3][0]

  return "http://chart.apis.google.com/chart?chtt=Translation+status&cht=bhs&chs=550x230&chd=t:" + values_string + \
         "&chco=C2EAAE,FFCC80,FFFF99,FF8080&chdl=Translated|Needs review|Needs update|Needs translation" + \
         u"&chxt=y,x&chxl=0:|euskara|català|español|english|deutsch|italiano|français&chds=0," + \
         str(total) + "&chxr=1,0," + str(total)
  
  

###############################################################
###############################################################

class MainHandler(webapp.RequestHandler):
  def get(self):
    charts = retrieve_charts()
    template_file = os.path.join(os.path.dirname(__file__), 'templates/index.html')
    template_values = {
      'charts': charts,
      'chart_url': chart_url(charts),
      'greeting': get_greeting(),
      'is_admin': users.is_current_user_admin(), 
    }

    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

###############################################################

class ListHandler(webapp.RequestHandler):
  def get(self):
    secure_page(self)

    page = int(self.request.get('page', '0'))
    translations, next = models.get_translations(page)

    if translations is None:
      error404(self)
      return

    if next:
      nexturi = '/translations/list?page=%s' % (page + 1)
    else:
      nexturi = None
    if page > 1:
      prevuri = '/translations/list?page=%s' % (page - 1)
    elif page == 1:
      prevuri = '/translations/list'
    else:
      prevuri = None

    template_file = os.path.join(os.path.dirname(__file__), 'templates/list.html')
    template_values = {
      'greeting': get_greeting(),
      'is_admin': users.is_current_user_admin(),
      'translations': translations,
      'nexturi': nexturi,
      'prevuri': prevuri,
    }

    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

###############################################################

class AddHandler(webapp.RequestHandler):
  def get(self):
    secure_page(self, need_admin=True)

    template_file = os.path.join(os.path.dirname(__file__), 'templates/add_translation.html')
    template_values = {
      'greeting': get_greeting(),
      'is_admin': users.is_current_user_admin(),
    }

    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

  def post(self): 
    secure_page(self, need_admin=True)

    result = models.createNewTranslation(self.request.get('msgid'))

    if result is None: #TODO show error somehow (see c2c)
      self.redirect('/translations/list')
    else:
      self.redirect('/translations/edit/'+str(result))

###############################################################

class EditHandler(webapp.RequestHandler):
  """ edit page - have a nice time decrypting the filter logic """
  def get(self, translationid, lang_filter=None, state_filter=None):
    secure_page(self)

    if lang_filter == 'all':
      lang_filter = None

    if not translationid is None and int(translationid) != 0:
      translation = models.get_translation(long(translationid))
      if translation is None or not translation.is_last_version:
        error404(self)
        return
    else: # no id given, find the first one and redirect
      id = models.get_next_translation_id(None, lang_filter, state_filter)
      if id is None: # They are now result to such filter !
        template_file = os.path.join(os.path.dirname(__file__), 'templates/edit_no_result.html')
        template_values = {
          'is_admin': users.is_current_user_admin(),
          'greeting': get_greeting()
        }
        self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))
        return
      redirect_url = '/translations/edit/' + str(id) + edit_filter_suffix(lang_filter, state_filter)
      self.redirect(redirect_url)
      return

    template_file = os.path.join(os.path.dirname(__file__), 'templates/edit_translation.html')
    template_values = {
      'greeting': get_greeting(),
      'is_admin': users.is_current_user_admin(),
      'translation': models.get_translation_tpl(translation),
      'logs': models.get_recent_logs(translation),
      'next_to_edit': models.get_next_translation_id(translation, lang_filter, state_filter),
      'url_suffix': edit_filter_suffix(lang_filter, state_filter),
      'status': self.request.get('status')
    }
    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

  """ save  changes to a translation """
  def post(self, translationid, lang_filter=None, state_filter=None):
    secure_page(self)
    result = models.updateTranslation(translationid, self.request)

    if result is None:
      status = '-1'
    else:
      status = '1'

    self.redirect('/translations/edit/'+translationid+edit_filter_suffix(lang_filter, state_filter)+'?status='+status)
    return

###############################################################

class ChangesHandler(webapp.RequestHandler):
  def get(self, lang_filter=None):
    secure_page(self)

    page = int(self.request.get('page', '0'))
    logs, next = models.get_logs(page, lang_filter)

    if logs is None:
      error404(self)
      return

    if next:
      nexturi = '/recentchanges?page=%s' % (page + 1)
    else:
      nexturi = None
    if page > 1:
      prevuri = '/recentchanges?page=%s' % (page - 1)
    elif page == 1:
      prevuri = '/recentchanges'
    else:
      prevuri = None

    template_file = os.path.join(os.path.dirname(__file__), 'templates/recent_changes.html')
    template_values = {
      'greeting': get_greeting(),
      'is_admin': users.is_current_user_admin(),
      'logs': logs,
      'nexturi': nexturi,
      'prevuri': prevuri,
    }

    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

###############################################################

class SearchHandler(webapp.RequestHandler):
  """ ajax search on msgids. Due to limitations of App Engine Datastore, matching is performed
      with the beginning of the string! """
  def get(self):
    if not self.request.get('search_text'):
      self.response.set_status(404, 'Not Found')
      return

    st = self.request.get('search_text')

    query = models.Translation.all() \
                  .filter('is_last_version =', True) \
                  .filter('msgid >=', st) \
                  .filter('msgid <', st + u"\ufffd")

    nb_results = query.count()

    if not nb_results:
      self.response.out.write('<ul><div class="feedback">no matching</div></ul>')
      return

    if query.count() > 10:
      self.response.out.write('<ul><div class="feedback">too many results<br />go on typing</div></ul>')
      return

    results = query.fetch(10)
    s = '<ul>'
    for result in results:
      s += '<li id="' + str(result.key().id()) + '">' + result.msgid + '</li>'
    s += '</ul>'
    self.response.out.write(s)

###############################################################

class FeedHandler(webapp.RequestHandler):
  def get(self):
    logs, extra = models.get_logs(page=0, page_size=30)

    template_file = os.path.join(os.path.dirname(__file__), 'templates/feed.xml')
    template_values = {
      'entries': logs
    }

    self.response.headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

###############################################################

class PoHandler(webapp.RequestHandler):
  def get(self, lang):
    translations = models.get_all_translations()

    template_file = os.path.join(os.path.dirname(__file__), 'templates/po.file')
    template_values = {
      'lang': lang,
      'translations': translations
    }

    self.response.headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))   

###############################################################

class HelpHandler(webapp.RequestHandler):
  def get(self):
    template_file = os.path.join(os.path.dirname(__file__), 'templates/help.html')
    template_values = {
      'greeting': get_greeting(),
      'is_admin': users.is_current_user_admin(),
    }

    self.response.out.write(Template(filename=template_file,lookup=mylookup).render_unicode(**template_values))

###############################################################

class NotFoundPageHandler(webapp.RequestHandler):
  def get(self):
    error404(self)

###############################################################
###############################################################

application = webapp.WSGIApplication(
  [
    ('/', MainHandler),
    ('/translations/list', ListHandler),
    ('/translations/add', AddHandler),
    ('/translations/edit/([0-9]+)', EditHandler),
    ('/translations/edit/([0-9]+)/filter/lang/(fr|it|de|en|es|ca|eu)', EditHandler),
    ('/translations/edit/([0-9]+)/filter/lang/(fr|it|de|en|es|ca|eu|all)/(translated|needs_review|needs_update|needs_translation)', EditHandler),
    ('/recentchanges', ChangesHandler),
    ('/recentchanges/(fr|it|de|en|es|ca|eu)', ChangesHandler),
    ('/translations/search', SearchHandler),
    ('/feed.rss', FeedHandler),
    ('/po/messages.(fr|it|de|en|es|ca|eu).po', PoHandler),
    ('/help', HelpHandler),
    ('/.*', NotFoundPageHandler)
  ], debug=True)

mylookup = TemplateLookup(directories=['templates'])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()


##############
"""
TODO
- pouvoir exporter les .po
- ecuperer les strings non traduites dnas un langage...
- pouvoir supprimer une entree, revenir aux versions précédentes... etc... --> garde rles logs apres suppression
cron de mails, ou alors feed rss...
echappements de strings
gérer le multiligne http://www.gnu.org/software/hello/manual/gettext/PO-Files.html
echappement de caractere et verifier que les params ok..;
pouvoir acceder aux vielles version
admin pour add et delete
pouvoir revenir a une version precedente
"""
