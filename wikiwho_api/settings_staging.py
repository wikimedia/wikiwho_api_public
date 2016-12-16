from .settings_base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE_CLASSES += ['debug_toolbar.middleware.DebugToolbarMiddleware']

SWAGGER_SETTINGS['VALIDATOR_URL'] = 'https://online.swagger.io/validator'

ALLOWED_HOSTS = ['193.175.238.88',
                 'www.wikiwho.net',
                 'wikiwho.net']

ONLY_READ_FROM_DB = True

# def custom_show_toolbar(request):
#     return True  # show toolbar always for staging

# DEBUG_TOOLBAR_CONFIG = {
#     'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
# }
