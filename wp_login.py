__author__ = 'ffl'

#!/usr/bin/python2.7

# Tested with MediaWiki 1.22.7

import requests
import json
import urllib

url ='https://en.wikipedia.org/w/api.php'

headers = {
    'User-Agent': 'Wikiwho API',
    'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'
}


session = requests.session()

user    = 'Fabian%20Fl%C3%B6ck@wikiwho'
passw   = 'o2l009t25ddtlefdt6cboctj8hk8nbfs'

params  = '?action=query&meta=tokens&type=login&format=json'

# Login request
r1 = session.post(url+params)
#print r1.json()
#r1 = json.loads(r1)
token = r1.json()["query"]["tokens"]["logintoken"]
token = urllib.quote(token)

print 'token', token
params2 = '?action=login&lgname=%s&lgpassword=%s&lgtoken=%s&format=json'% (user,passw,token)
#print 'params2', params2
# Confirm token; should give "Success"
r2 = session.post(url+params2)
print r2.json()

# Try accessing a private MediaWiki page
#r3 = requests.get(baseurl+'index.php/PrivateTest',
#        auth=(authu,authp),cookies=r2.cookies)

# Display the HTML
#print r3.text
