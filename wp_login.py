__author__ = 'ffl'

#!/usr/bin/python2.7

# Tested with MediaWiki 1.22.7

import requests

user    = 'Fabian%20Fl%C3%B6ck'
passw   = 'rumkugeln'
authu   = 'apacheuser'    # For Apache Basic Auth
authp   = 'apachepass'    # For Apache Basic Auth
baseurl = 'https://en.wikipedia.org/w/'
params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)

# Login request
r1 = requests.post(baseurl+'api.php'+params,auth=(authu,authp))
token = r1.json()['login']['token']
params2 = params+'&lgtoken=%s'% token

# Confirm token; should give "Success"
r2 = requests.post(baseurl+'api.php'+params2,auth=(authu,authp),cookies=r1.cookies)
print r2.json()['login']['result']

# Try accessing a private MediaWiki page
#r3 = requests.get(baseurl+'index.php/PrivateTest',
#        auth=(authu,authp),cookies=r2.cookies)

# Display the HTML
#print r3.text