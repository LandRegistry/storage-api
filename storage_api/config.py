import os

FLASK_LOG_LEVEL = os.environ['LOG_LEVEL']

COMMIT = os.environ['COMMIT']
DEFAULT_TIMEOUT = int(os.environ['DEFAULT_TIMEOUT'])

APP_NAME = os.environ['APP_NAME']

# Type the API will use for storage, either file or S3
STORAGE_TYPE = os.environ['STORAGE_TYPE']

# Location the API will use for storage, either local or S3
FILE_STORAGE_LOCATION = os.environ['FILE_STORAGE_LOCATION']

AUTHENTICATION_API_URL = os.environ['AUTHENTICATION_API_URL']
AUTHENTICATION_API_ROOT = os.environ['AUTHENTICATION_API_ROOT']

MAX_HEALTH_CASCADE = os.environ['MAX_HEALTH_CASCADE']

FILE_EXTERNAL_URL_BASE = os.environ['FILE_EXTERNAL_URL_BASE']

CLAMD_HOST = os.getenv("CLAMD_HOST")
CLAMD_PORT = int(os.getenv("CLAMD_PORT", "0"))

DEPENDENCIES = {
    'authentication-api': AUTHENTICATION_API_ROOT
}

S3_BUCKET = os.environ['S3_BUCKET']
S3_URL_EXPIRE_IN_SECONDS = os.environ['S3_URL_EXPIRE_IN_SECONDS']

LOGCONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            '()': 'storage_api.extensions.JsonFormatter'
        },
        'audit': {
            '()': 'storage_api.extensions.JsonAuditFormatter'
        }
    },
    'filters': {
        'contextual': {
            '()': 'storage_api.extensions.ContextualFilter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['contextual'],
            'stream': 'ext://sys.stdout'
        },
        'audit_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'audit',
            'filters': ['contextual'],
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'storage_api': {
            'handlers': ['console'],
            'level': FLASK_LOG_LEVEL
        },
        'audit': {
            'handlers': ['audit_console'],
            'level': 'INFO'
        }
    }
}
