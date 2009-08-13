#!/usr/bin/python
import code
import getpass
import sys

sys.path.append("/home/popeye/google_appengine")
sys.path.append("/home/popeye/google_appengine/lib/yaml/lib")
sys.path.append("/home/popeye/c2ci18n")

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db
from google.appengine.api import users

def auth_func():
  return raw_input('Username:'), getpass.getpass('Password:')

if len(sys.argv) < 2:
  print "Usage: %s app_id [host]" % (sys.argv[0],)
app_id = sys.argv[1]
if len(sys.argv) > 2:
  host = sys.argv[2]
else:
  host = '%s.appspot.com' % app_id

remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

import models

file = open('/home/popeye/c2ci18n/tools/msg_strings','r')
lines = file.readlines()

batch_size = 10
items_count = len(lines)

items = lines[0:batch_size]
query_count = 0
while items:
  to_put = []
  for item in items:
    strings = item.split("\t")
    # create translation
    translation = models.Translation(msgid=strings[0].decode('utf-8'))
    translation.comment = ''
    translation.fr_comment = ''
    translation.it_comment = ''
    translation.de_comment = ''
    translation.en_comment = ''
    translation.es_comment = ''
    translation.ca_comment = ''
    translation.eu_comment = ''
    translation.version = 1
    translation.is_last_version = True
    #translation.creator = users.User("initialimport")
    translation.fr_state = 'translated'
    translation.it_state = 'translated'
    translation.de_state = 'translated'
    translation.en_state = 'translated'
    translation.es_state = 'translated'
    translation.ca_state = 'translated'
    translation.eu_state = 'translated'
    translation.fr = strings[1].decode('utf-8')
    translation.it = strings[2].decode('utf-8')
    translation.de = strings[3].decode('utf-8')
    translation.en = strings[4].decode('utf-8')
    translation.es = strings[5].decode('utf-8')
    translation.ca = strings[6].decode('utf-8')
    translation.eu = strings[7].decode('utf-8')

    to_put.append(translation)
  if to_put:
    print 'upload #' + str(query_count)
    db.put(to_put)
  query_count += 1
  items = lines[batch_size*query_count:batch_size*(query_count+1)]

print 'creating counters'

counter = models.Counter(lang='fr')
counter.translated = items_count
counter.put()
counter = models.Counter(lang='it')
counter.translated = items_count
counter.put()
counter = models.Counter(lang='de')
counter.translated = items_count
counter.put()
counter = models.Counter(lang='en')
counter.translated = items_count
counter.put()
counter = models.Counter(lang='es')
counter.translated = items_count
counter.put()
counter = models.Counter(lang='ca')
counter.translated = items_count
counter.put()
counter = models.Counter(lang='eu')
counter.translated = items_count
counter.put()


print 'END'
