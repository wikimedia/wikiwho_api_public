

#!/usr/bin/python2.7



__author__ = 'psinger, ffloeck'


import requests

user    = 'Fabian%20Fl%C3%B6ck'
passw   = 'rumkugeln'
authu   = 'apacheuser'    # For Apache Basic Auth
authp   = 'apachepass'    # For Apache Basic Auth
baseurl = 'https://en.wikipedia.org/w/'
params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)

url = 'https://en.wikipedia.org/w/api.php'

headers = {
        'User-Agent': 'Wikiwho API',
        'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'
}

para = {'titles':"Graz", 'action':'query', 'prop':'revisions', 'rvprop':'content|ids|timestamp|sha1|comment|flags|user|userid', 'rvlimit':'max', 'format':'json', 'continue':'', 'rvdir':'newer'}

#result = requests.get(url=url, headers=headers, params=params, auth=(user,passw)).json()

#print len(result["query"]["pages"]['48946']["revisions"])

s = requests.session()

params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)
r1 = s.post(baseurl+'api.php'+params,auth=(authu,authp))
token = r1.json()['login']['token']
params2 = params+'&lgtoken=%s'% token

# Confirm token; should give "Success"
r2 = s.post(baseurl+'api.php'+params2,auth=(authu,authp),cookies=r1.cookies)
print r2.json()['login']['result']
#print r2.json().keys()

result = s.get(url=url, headers=headers, params=para).json()

print len(result["query"]["pages"]['48946']["revisions"])
print result["limits"]

# Login request
#ir1 = requests.post(baseurl+'api.php'+params,auth=(authu,authp))
#token = r1.json()['login']['token']
#params2 = params+'&lgtoken=%s'% token
#print r1.cookies
# Confirm token; should give "Success"
#r2 = requests.post(baseurl+'api.php'+params2,auth=(authu,authp),cookies=r1.cookies)
#print r2.json()['login']['result']
