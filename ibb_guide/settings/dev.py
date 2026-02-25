from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# Default SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email - Console Backend (Prints emails to the terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST_USER = 'test@example.com'  # Dummy value
DEFAULT_FROM_EMAIL = 'dlib-ibb@example.com'

# Skip email verification in development - auto-login after registration
SKIP_EMAIL_VERIFICATION = True

# Logic to bypass heavy security in dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Allow cross-origin requests for testing tunnels
CSRF_TRUSTED_ORIGINS = [
    'https://*.serveousercontent.com',
    'https://*.serveo.net',
    'https://*.loca.lt',
    'https://*.ngrok.io',
    'https://*.ngrok-free.app',
]

# ==========================================
# Development Overrides - No Redis Required
# ==========================================

# 1. Cache - Use Local Memory
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# 2. Sessions - Use Database
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# 3. Celery - Use In-Memory Broker
CELERY_BROKER_URL = 'memory://'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# 4. Channels - Use In-Memory Layer (if installed)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
