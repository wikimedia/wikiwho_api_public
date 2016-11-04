from .settings_base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['local_host', '127.0.0.1']
INTERNAL_IPS = ['127.0.0.1']

PICKLE_FOLDER = 'tmp_pickles'  # ''pickle_api'
PICKLE_FOLDER_2 = 'tmp_pickles'  # ''../disk2/pickle_api_2'

INSTALLED_APPS += ['debug_toolbar',
                   'debug_panel']

MIDDLEWARE_CLASSES += ['debug_panel.middleware.DebugPanelMiddleware']

SWAGGER_SETTINGS['VALIDATOR_URL'] = 'https://online.swagger.io/validator'

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }
