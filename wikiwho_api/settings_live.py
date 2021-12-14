import raven

from .settings_base import *

# TODO https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
SERVER_LEVEL = LEVEL_PRODUCTION

ACTIONS_LOG = '/var/log/django/actions_log'
ACTIONS_MAX_WORKERS = 12

EVENTS_STREAM_LOG = '/var/log/django/events_streamer'

SWAGGER_SETTINGS['VALIDATOR_URL'] = 'https://online.swagger.io/validator'

ALLOWED_HOSTS = ['193.175.238.88',
                 # '180.163.113.82',
                 'www.wikiwho.net',
                 'api.wikiwho.net',
                 'wikiwho.net',
                 'svko-css-wikiwho.gesis.intra']

ONLY_READ_ALLOWED = False

# Whether to use a secure cookie for the CSRF cookie. If this is set to True, the cookie will be marked as “secure,”
# which means browsers may ensure that the cookie is only sent with an HTTPS connection.
CSRF_COOKIE_SECURE = True
# Whether to use a secure cookie for the session cookie. If this is set to True, the cookie will be marked as “secure,”
# which means browsers may ensure that the cookie is only sent under an HTTPS connection.
SESSION_COOKIE_SECURE = True

# CONN_MAX_AGE = TODO # Persistent connections avoid the overhead of re-establishing a connection to the database in
# each request. They’re controlled by the CONN_MAX_AGE parameter which defines the maximum lifetime of a connection.
# It can be set independently for each database.


# Sentry
INSTALLED_APPS += [
    'raven.contrib.django.raven_compat',
]

# Default logging for Django. This sends an email to the site admins on every
# HTTP 500 error. Depending on DEBUG, all other log records are either sent to
# the console (DEBUG=True) or discarded (DEBUG=False) by means of the
# require_debug_true filter.
# https://docs.djangoproject.com/en/1.10/topics/logging/#examples
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(server_time)s] %(message)s',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/var/log/django/django.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 10,
        },
        'sentry': {
            'level': 'ERROR',  # To capture more than ERROR, change to WARNING, INFO, etc.
            'filters': ['require_debug_false'],
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': 'x'},
        }
    },
    'loggers': {
        # print(logging.Logger.manager.loggerDict) to list all loggers
        'django': {
            # 'handlers': ['console', 'mail_admins'],
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        }
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    }
}
