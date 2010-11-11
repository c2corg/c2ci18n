# -*- coding: utf-8 -*-

import difflib
import string
import datetime
import time
import relativedelta
import cgi

#######################################################
def relative_time(date):
  delta = relativedelta.relativedelta(datetime.datetime.now(), date)

  if delta.years == 1:
    time = 'about 1 year ago'
  elif delta.years > 1:
    time = 'about %s years ago' % delta.years
  elif delta.months == 1:
    time = 'about 1 month ago'
  elif delta.months > 1:
    time = 'about %s months ago' % delta.months
  elif delta.days == 1:
    time = 'about 1 day ago'
  elif delta.days > 1:
    time = 'about %s days ago' % delta.days
  elif delta.hours == 1:
    time = 'about 1 hour ago'
  elif delta.hours > 1:
    time = 'about %s hours ago' % delta.hours
  elif delta.minutes > 1:
    time = '%s minutes ago' % delta.minutes
  else:
    time = 'recently'

  return time

#######################################################
def check_value(t,l,s):
  """ determine if a radio button should be checked """
  if t[l+'_state'] == s:
    return ' checked="checked"'
  else:
    return ''

########################################################
def html_diff(strings, standalone=False):
  """ produce html code to show differences between two strings """
  #¶
  out = ''
  l = []

  for s in strings:
    s = s.replace('\n', u'¶')
    l.append(insert_spaces(s.split(' ')))

  delend = '</del>'
  insend = '</ins>'
  if standalone == True:
    delstart = '<del style="background-color: #ffb3b3;">'
    insstart = '<ins style="background-color: #c2eaae;">'
  else:
    delstart = '<del class="diff modified">'
    insstart = '<ins class="diff modified">'

  differ = difflib.SequenceMatcher(None, l[0], l[1])
  for e in differ.get_opcodes():
    if e[0] == "replace":
      out += (delstart + ''.join(l[0][e[1]:e[2]]) + delend + insstart + ''.join(l[1][e[3]:e[4]]) + insend)
    elif e[0] == "delete":
      out += (delstart + ''.join(l[0][e[1]:e[2]]) + delend)
    elif e[0] == "insert":
      out += (insstart + ''.join(l[1][e[3]:e[4]]) + insend)
    elif e[0] == "equal":
      out += (''.join(l[1][e[3]:e[4]]))

  return out.replace(u'¶', u'¶<br />')

#########################################################
def insert_spaces(l):
  for i in range(0,len(l)-1):
    l.insert(i * 2 + 1, ' ')
  return l

#########################################################
def escape_n(s):
  return cgi.escape(s).replace('\n', '<br />')

#########################################################
def escape_po(s):
  """Trailing linebreaks are stripped. Special characters are handled.
     Internal linebreaks are handled for better msgstr display"""
  return s.replace('\\', '\\\\').replace('"', '\\"').strip('\r\n').replace('\r\n', '\\n"\n"')

#########################################################
def escape_po_comment(s):
  return s.replace('\n', '\n# ')

#########################################################
def rfc3339date(date):
  """Formats the given date in RFC 3339 format for feeds."""
  if not date: return ''
  date = date + datetime.timedelta(seconds=-time.timezone)
  if time.daylight:
    date += datetime.timedelta(seconds=time.altzone)
  return date.strftime('%Y-%m-%dT%H:%M:%SZ')

#########################################################
def get_actual_translation(translation, lang, warning=False):
  """
  if no fr, missing
  if no it, en
  if no en, fr
  if no de, en
  if no es, en
  if no ca, es
  if no eu, es
  """
  if warning:
    error_msg = '# [WARNING] ' + lang + ' translation used'
  elif getattr(translation, lang+'_state') != 'translated':
    error_msg = '# [WARNING] ' + getattr(translation, lang+'_state')
  else:
    error_msg = ''

  if lang == 'fr':
    if translation.fr_state == 'needs_translation':
      return [ 'MISSING TRANSLATION', '# [ERROR] no available translation' ]
    else:
      return [ translation.fr, error_msg ]

  if lang == 'it':
    if translation.it_state == 'needs_translation':
      return get_actual_translation(translation, 'en', True)
    else:
      return [ translation.it, error_msg ]

  if lang == 'en':
    if translation.en_state == 'needs_translation':
      return get_actual_translation(translation, 'fr', True)
    else:
      return [ translation.en, error_msg ]

  if lang == 'de':
    if translation.de_state == 'needs_translation':
      return get_actual_translation(translation, 'en', True)
    else:
      return [ translation.de, error_msg ]

  if lang == 'es':
    if translation.es_state == 'needs_translation':
      return get_actual_translation(translation, 'en', True)
    else:
      return [ translation.es, error_msg ]

  if lang == 'ca':
    if translation.ca_state == 'needs_translation':
      return get_actual_translation(translation, 'es', True)
    else:
      return [ translation.ca, error_msg ]

  if lang == 'eu':
    if translation.eu_state == 'needs_translation':
      return get_actual_translation(translation, 'es', True)
    else:
      return [ translation.eu, error_msg ]
