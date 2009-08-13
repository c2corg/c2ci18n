# -*- coding: utf-8 -*-

import datetime
import hashlib
import copy
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

LIST_PAGE_SIZE = 30
LOG_PAGE_SIZE = 20
LOG_LIMIT = 10
LANGS = ['fr','it','de','en','es','ca','eu']
STATUSES = ['translated','needs_update','needs_review','needs_translation']

########################################################################
########################################################################

class Translation(db.Model):
  """a translation - can be an archived version"""
  msgid = db.StringProperty(required=True)
  comment = db.TextProperty()
  fr = db.TextProperty()
  fr_comment = db.TextProperty()
  it = db.TextProperty()
  it_comment = db.TextProperty()
  de = db.TextProperty()
  de_comment = db.TextProperty()
  en = db.TextProperty()
  en_comment = db.TextProperty()
  es = db.TextProperty()
  es_comment = db.TextProperty()
  ca = db.TextProperty()
  ca_comment = db.TextProperty()
  eu = db.TextProperty()
  eu_comment = db.TextProperty()
  fr_state = db.StringProperty(default='translated', choices=STATUSES)
  it_state = db.StringProperty(default='translated', choices=STATUSES)
  de_state = db.StringProperty(default='translated', choices=STATUSES)
  en_state = db.StringProperty(default='translated', choices=STATUSES)
  es_state = db.StringProperty(default='translated', choices=STATUSES)
  ca_state = db.StringProperty(default='translated', choices=STATUSES)
  eu_state = db.StringProperty(default='translated', choices=STATUSES)
  version = db.IntegerProperty()
  is_last_version = db.BooleanProperty()
  created = db.DateTimeProperty(auto_now=True)
  creator = db.UserProperty()

class Log(db.Model):
  """used to log changes - one log per language"""
  translation_ref = db.ReferenceProperty(Translation)
  translation_msgid = db.StringProperty()
  translation_version = db.IntegerProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  user = db.UserProperty()
  lang = db.StringProperty(choices=LANGS+['creation', 'general'])
  comment_changed = db.BooleanProperty()
  old_comment = db.TextProperty()
  new_comment = db.TextProperty()
  text_changed = db.BooleanProperty()
  old_text = db.TextProperty()
  new_text = db.TextProperty()
  state_changed = db.BooleanProperty(default=False)
  old_state = db.TextProperty()
  new_state = db.TextProperty()

class Counter(db.Model):
  """Used to keep track of count of translated and untranslated strings for each language"""
  lang = db.StringProperty(choices=LANGS, required=True)
  translated = db.IntegerProperty(default=0)
  needs_update = db.IntegerProperty(default=0)
  needs_review = db.IntegerProperty(default=0)
  needs_translation = db.IntegerProperty(default=0)

########################################################################
########################################################################

def incrementCounter(lang, status):
  counter = Counter.all().filter('lang =', lang).get()
  if not counter:
    counter = Counter(lang=lang)
  def txn():
    setattr(counter, status, getattr(counter, status) + 1)
    counter.put()
  db.run_in_transaction(txn)

########################################################################

def decrementCounter(lang, status):
  counter = Counter.all().filter('lang =', lang).get()
  if not counter:
    counter = Counter(lang=lang)
  def txn():
    setattr(counter, status, getattr(counter, status) - 1)
    counter.put()
  db.run_in_transaction(txn)

########################################################################

def createLog(translation, user, lang, fields, values):
  log = Log()

  log.translation_ref = translation['key']
  log.translation_msgid = translation['msgid']
  log.translation_version = translation['version']
  log.user = user
  log.lang = lang

  if not fields is None:
    for field in fields:
      setattr(log, field + '_changed', True)
      setattr(log, 'old_' + field, values['old_' + field])
      setattr(log, 'new_' + field, values['new_' + field])

  log.put()

########################################################################

def get_recent_logs(translation):
  return Log.all().filter('translation_ref =', translation).order('-date').fetch(10)

########################################################################

def translation_ref(translation):
  return { 'key': translation.key(), 'msgid': translation.msgid, 'version': translation.version }

########################################################################

def get_translation_tpl(translation):
  return {
      'id': translation.key().id(),
      'msgid': translation.msgid,
      'comment': translation.comment,
      'fr': translation.fr,
      'fr_comment': translation.fr_comment,
      'fr_state': translation.fr_state,
      'it': translation.it,
      'it_comment': translation.it_comment,
      'it_state': translation.it_state,
      'de': translation.de,
      'de_comment': translation.de_comment,
      'de_state': translation.de_state,
      'en': translation.en,
      'en_comment': translation.en_comment,
      'en_state': translation.en_state,
      'es': translation.es,
      'es_comment': translation.es_comment,
      'es_state': translation.es_state,
      'ca': translation.ca,
      'ca_comment': translation.ca_comment,
      'ca_state': translation.ca_state,
      'eu': translation.eu,
      'eu_comment': translation.eu_comment,
      'eu_state': translation.eu_state
    }

########################################################################

def make_translation_archive(translation):
  def txn():
    new = Translation(msgid=translation.msgid)
    new.created = translation.created
    new.creator = translation.creator
    new.is_last_version = False
    new.version = translation.version
    new.comment = translation.comment
    new.fr = translation.fr
    new.fr_comment = translation.fr_comment
    new.fr_state = translation.fr_state
    new.it = translation.it
    new.it_comment = translation.it_comment
    new.it_state = translation.it_state
    new.de = translation.de
    new.de_comment = translation.de_comment
    new.de_state = translation.de_state
    new.en = translation.en
    new.en_comment = translation.en_comment
    new.en_state = translation.en_state
    new.es = translation.es
    new.es_comment = translation.es_comment
    new.es_state = translation.es_state
    new.ca = translation.ca
    new.ca_comment = translation.ca_comment
    new.ca_state = translation.ca_state
    new.eu = translation.eu
    new.eu_comment = translation.eu_comment
    new.eu_state = translation.eu_state
    new.put()
    return new.key().id()
  return db.run_in_transaction(txn)

########################################################################

def apply_list_filter(query, lang_filter=None, state_filter=None):
  """ this one is a bit simpler than get_next_translation_id, since
      we don't allow state_filter without lang_filter (see urls in main.py) """
  if lang_filter is None:
    return query # this shouldn't happen

  if not state_filter is None:
    sf = [ state_filter ]
  else:
    sf = [ 'needs_translation', 'needs_review', 'needs_update' ]

  return query.filter(lang_filter + '_state IN', sf)

########################################################################

def get_translations(page=0, lang_filter=None, state_filter=None):
  """ translations list (paginated) """
  assert page >=0
  extra = None

  #fetch offset limit=1000
  if page*LIST_PAGE_SIZE > 1000:
    last_item = None
    while page*LIST_PAGE_SIZE > 1000:
      if last_item is None:
        last_item = apply_list_filter(Translation.all().order('msgid'), lang_filter, state_filter) \
                    .filter('is_last_version =', True).fetch(1, 1000)
      else:
        last_item = apply_list_filter(Translation.all().order('msgid'), lang_filter, state_filter) \
                    .filter('msgid >=', last_item[0].msgid) \
                    .filter('is_last_version =', True).fetch(1, 1000)
      if not last_item:
        return None, None
      page = page - (1000 / LIST_PAGE_SIZE)

    translations = apply_list_filter(Translation.all().order('msgid'), lang_filter, state_filter) \
                   .filter('msgid >=', last_item[0].msgid) \
                   .filter('is_last_version =', True).fetch(LIST_PAGE_SIZE+1, page*LIST_PAGE_SIZE)
  ## no worry about offset limit
  else:
    translations = apply_list_filter(Translation.all().order('msgid'), lang_filter, state_filter) \
                   .filter('is_last_version =', True).fetch(LIST_PAGE_SIZE+1, page*LIST_PAGE_SIZE)

  if len(translations) > LIST_PAGE_SIZE:
    extra = translations[-1]
    translations = translations[:LIST_PAGE_SIZE]

  translations_tpl = []
  for translation in translations:
    translations_tpl.append(get_translation_tpl(translation))
  return translations_tpl, extra

########################################################################

def get_all_translations():
  """ get ALL translations """
  size = 500
  counter = 0
  translations = []

  while counter == 0 or len(some_translations) > size:
    some_translations = Translation.all().order('msgid').filter('is_last_version =', True).fetch(size+1, counter*size)
    counter +=1
    translations += some_translations

  return translations

########################################################################

def get_translation(id):
  """ returns a translation object, given its id """
  return Translation.get_by_id(id)

########################################################################

def get_log(id):
  """ returns a log object, given its id """
  return Log.get_by_id(id)

########################################################################

def get_next_translation_id(translation=None, lang_filter=None, state_filter=None):
  """ returns next translation to edit, given the filter - enjoy the logic
      note: if id given, but no results, try to go back to beginning of the list """

  query = Translation.all().order('msgid').filter('is_last_version =', True)

  if not translation is None:
    query = query.filter('msgid >', translation.msgid)

  if not state_filter is None:
    sf = [ state_filter ]
  else:
    sf = [ 'needs_translation', 'needs_review', 'needs_update' ]

  if not lang_filter is None: # lang filter with or without state filter
    query = query.filter(lang_filter + '_state IN', sf)

  elif not state_filter is None: # state filter alone. There is no 'OR', so it's more complicated
    results = []
    for lang in LANGS:
      subquery = copy.deepcopy(query)
      subresult = subquery.filter(lang + '_state =', state_filter).get()
      if not subresult is None:
        results.append(subresult)
    if len(results) == 0:
      if not translation is None: # If no result, but a translation id was given, try to go back to beginning of the list
        return get_next_translation_id(None, lang_filter, state_filter)
      else:
        return None
    else:
      return results[0].key().id()

  next = query.get()

  if next is None:
    if not translation is None: # If no result, but a translation id was given, try to go back to beginning of the list
      return get_next_translation_id(None, lang_filter, state_filter)
    else:
      return None
  else:
    return next.key().id()

########################################################################

def get_logs(page=0, lang_filter=None, page_size=LOG_PAGE_SIZE):
  """ returns page_size logs per page in reverse date order
      can be filtered on lang """
  assert page >=0
  extra = None

  # we limit this to the last 1000 log, so as not to worry with fetch offset limit
  # Anyway, who cares about logs that old?

  if page*page_size > 1000:
    return None, None

  query = Log.all().order('-date')
  if not lang_filter is None:
    query = query.filter('lang IN', [lang_filter, 'general', 'creation'])
  logs = query.fetch(page_size+1, page*page_size)
  if len(logs) > page_size:
    extra = logs[-1]
    translations = logs[:page_size]

  if page*page_size >= 1000 - page_size and page*page_size < 1000:
    extra = None

  return logs, extra

########################################################################

def createNewTranslation(msgid):
  if not msgid or Translation.all().filter('msgid =', msgid).count() != 0:
    return None

  try:
    translation = Translation(msgid=msgid)
    translation.version = 1
    translation.is_last_version = True

    if users.get_current_user():
      translation.creator = users.get_current_user()

    setattr(translation, 'comment', '')

    for lang in LANGS:
      setattr(translation, lang+ '_state', 'needs_translation')
      setattr(translation, lang, '')
      incrementCounter(lang, 'needs_translation')
      setattr(translation, lang + '_comment', '')

    translation.put()

    createLog(translation_ref(translation), users.get_current_user(), 'creation', None, None)
    return translation.key().id()
  except db.Error:
    return None

########################################################################

def updateTranslation(id, request):
  last_translation = Translation.get_by_id(long(id))

  if not last_translation:
    return None

  archive_key = make_translation_archive(last_translation)

  last_translation.version += 1
  if users.get_current_user():
    last_translation.creator = users.get_current_user()
  else:
    last_translation.creator = users.User("anonymous@anonymous.org")

  #last_translation.created = 

  # retrieve changes
  has_changes = False

  if request.get('comment') != last_translation.comment:
    has_changes = True
    createLog(translation_ref(last_translation), users.get_current_user(), 'general', ['comment'],
              { 'old_comment': last_translation.comment, 'new_comment': request.get('comment') })
    last_translation.comment = request.get('comment') 
    
  for lang in LANGS:
      lang_has_changes = False

      attributes = { 'text': lang, 'comment': lang + '_comment', 'state': lang + '_state' }
      changed_fields = []
      changed_values = {}

      for attr_type, attribute in attributes.items():
        if getattr(last_translation, attribute) != request.get(attribute):
          # if state changed, update counters
          if attribute == lang + '_state':
            incrementCounter(lang, request.get(attribute))
            decrementCounter(lang, getattr(last_translation, attribute))
          
          changed_fields.append(attr_type)
          changed_values['old_' + attr_type] = getattr(last_translation, attribute)
          changed_values['new_' + attr_type] = request.get(attribute)

          setattr(last_translation, attribute, request.get(attribute))
          lang_has_changes = True
          has_changes = True

      if lang_has_changes:
        createLog(translation_ref(last_translation),
                  users.get_current_user(), lang, changed_fields, changed_values)


  # No changes
  if not has_changes:
    Translation.get_by_id(long(archive_key)).delete()
    return None

  last_translation.put()
  return last_translation.key().id()
#  except db.Error: TODO
#    return None
#run in transaction?
