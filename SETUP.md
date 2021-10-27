## Notes from trying to stand up app

### Requirements

* I had to edit the line `-e git+git@github.com:gesiscss/wikiwho_chobj.git#egg=wikiwho_chobj`. It's public, so the equivalent is `-e git://github.com/gesiscss/wikiwho_chobj.git#egg=wikiwho_chobj`
* I had to relax the pytest version requirement (in both requirements.txt and requirements_test.txt).
* I'm using a virtualenv, so I added `env` to the 
* Installation didn't work until I had an up-to-date version of `pip3`.
* I had to install some build dependencies (`sudo apt-get install python3-dev graphviz libgraphviz-dev pkg-config`) to be able to install the `requirements_local.txt`.
* To get versions of all the dependencies that are compatible with each other, I had to do both requirements files in one command: `pip3 install -r requirements.txt -r requirements_local.txt`

### Running the server
* Can't start the server initially (`python3 manage.py runserver localhost:8000`) because there is no wikiwho_api/settings.py 
  * Copied settings_local.py to settings.py, then added `SECRET_KEY = 'secret'`

* I had to add DATABASES to settings.py, and create the matching user+password and database in postgres:

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', 
        'NAME': 'wikiwho',                     
        'USER': 'wikiwho',
        'PASSWORD': 'wikiwho',
        'HOST': 'localhost'
    }
}
```
