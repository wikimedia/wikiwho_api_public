import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
    'api',
    'base',
    'django_extensions',
    'wikiwho',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wikiwho_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wikiwho_api.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGE_CODE = 'en'

# LANGUAGES = (
#     ('en', _('English')),
#     ('de', _('German')),
# )
# LOCALE_PATHS = (
#     os.path.join(BASE_DIR, 'locale').replace('\\', '/'),
# )

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static').replace('\\', '/')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "assets"),
    # '/var/www/static/',
)

# MEDIA_ROOT = os.path.join(BASE_DIR, 'media').replace('\\', '/')
# MEDIA_URL = '/media/'

# CACHE
def make_key(key, key_prefix, version):
    return ':'.join([key_prefix, str(version), key])

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'localhost:11211',
    #     'LOCATION': 'unix:/tmp/memcached.sock',
    # One excellent feature of Memcached is its ability to share a cache over multiple servers. This means you can run
    # Memcached daemons on multiple machines, and the program will treat the group of machines as a single cache,
    # without the need to duplicate cache values on each machine.
    #     'LOCATION': [
    #         '172.19.26.240:11211',
    #         '172.19.26.242:11211',
    #     ]
        'TIMEOUT': None,  # default is 300 in seconds
        'KEY_PREFIX': '',
        'VERSION': '',
        'KEY_FUNCTION': 'wikiwho_api.settings_base.make_key',
    }
}


# REST_FRAMEWORK and Swagger UI
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '2000/day',
        'burst': '100/minute'
    },
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
}

SWAGGER_SETTINGS = {
    'LOGIN_URL': 'rest_framework:login',
    'LOGOUT_URL': 'rest_framework:logout',
    'USE_SESSION_AUTH': True,
    'SECURITY_DEFINITIONS': {
        'basic': {
            'type': 'basic'  # The security definitions configures which authentication methods can be used by Swagger.
            # The schemes types currently supported by the OpenAPI 2.0 spec are basic, apiKey and oauth2.
            # For more information on available options, please consult the OpenAPI Security Object Definition.
        }
    },
    'OPERATIONS_SORTER': 'alpha',  # or 'method'
    'APIS_SORTER': 'alpha',
    'DOC_EXPANSION': 'list',
    # 'JSON_EDITOR': True,
    # 'SHOW_REQUEST_HEADERS': True,
    # 'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
    # 'VALIDATOR_URL': 'https://online.swagger.io/validator/',
}

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_CACHE_ERRORS': False
}

# where pickles are saved
PICKLE_FOLDER = 'pickle_api'
PICKLE_FOLDER_2 = '../disk2/pickle_api_2'

LOG_PARSING_PATTERN = '#######*******#######'
REVISION_COUNT_CACHE_LIMIT = 100
DELETED_CONTENT_THRESHOLD_LIMIT = 5
ONLY_READ_FROM_DB = False

# Wikipedia
WP_HEADERS_USER_AGENT = 'Wikiwho API'
WP_HEADERS_FROM = 'philipp.singer@gesis.org, fabian.floeck@gesis.org and kenan.erdogan@gesis.org'
