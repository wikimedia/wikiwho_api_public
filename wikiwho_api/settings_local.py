from .settings_base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

ALLOWED_HOSTS = ['local_host', '127.0.0.1']
INTERNAL_IPS = ['127.0.0.1']

# PICKLE_FOLDER = 'tmp_pickles'
PICKLE_FOLDER_EN = 'tmp_pickles/en'
if not os.path.exists(PICKLE_FOLDER_EN):
    os.mkdir(PICKLE_FOLDER_EN)
PICKLE_FOLDER_EU = 'tmp_pickles/eu'
if not os.path.exists(PICKLE_FOLDER_EU):
    os.mkdir(PICKLE_FOLDER_EU)

INSTALLED_APPS += ['debug_toolbar',
                   'debug_panel']

MIDDLEWARE_CLASSES += ['debug_panel.middleware.DebugPanelMiddleware']

SWAGGER_SETTINGS['VALIDATOR_URL'] = 'https://online.swagger.io/validator'

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }
