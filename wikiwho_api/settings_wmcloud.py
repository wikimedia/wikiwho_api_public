# import raven

from .settings_base import *

# TODO https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
SERVER_LEVEL = LEVEL_PRODUCTION

ACTIONS_LOG = '/var/log/django/actions_log'
ACTIONS_MAX_WORKERS = 12
EVENTS_STREAM_LOG = '/var/log/django/events_streamer'

SWAGGER_SETTINGS['VALIDATOR_URL'] = 'https://online.swagger.io/validator'

ALLOWED_HOSTS = ['wikiwho-api.wmcloud.org', 'wikiwho.wmflabs.org']

ONLY_READ_ALLOWED = False

ACTIONS_LANGUAGES = ['tr', 'eu', 'es', 'de', 'en', 'fr', 'it', 'hu', 'id', 'ja', 'pt', 'nl']

# On pickle_storage volume, mounted to /pickles
PICKLE_FOLDER_EN = '/pickles/en'
PICKLE_FOLDER_EU = '/pickles/eu'
PICKLE_FOLDER_ES = '/pickles/es'
PICKLE_FOLDER_DE = '/pickles/de'
PICKLE_FOLDER_TR = '/pickles/tr'

# On pickle_storage02 volume, mounted to /pickles-02
PICKLE_FOLDER_FR = '/pickles-02/fr'
PICKLE_FOLDER_IT = '/pickles-02/it'
PICKLE_FOLDER_HU = '/pickles-02/hu'
PICKLE_FOLDER_ID = '/pickles-02/id'
PICKLE_FOLDER_JA = '/pickles-02/ja'
PICKLE_FOLDER_PT = '/pickles-02/pt'
PICKLE_FOLDER_NL = '/pickles-02/nl'

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['anon'] = '100/sec'
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['burst'] = '100/sec'
