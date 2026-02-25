"""
Base settings for ibb_guide project.
"""
from pathlib import Path
import os
from decouple import config
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Adjust for new settings location: parent.parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dummy-key')

# Default to False for safety, override in dev.py
DEBUG = config('DEBUG', default=False, cast=bool)

# Security: Default to localhost only, require explicit config in production
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    # Third Party
    'jazzmin',
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'rest_framework_simplejwt',
    'axes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',  # Required for allauth
    'django_filters',
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # Custom Apps
    'users',
    'places',
    'interactions',
    'management',
    'communities',
    'surveys',
    'events',
    # Celery
    'django_celery_results',
    # Image Optimization
    'sorl.thumbnail',
    'mathfilters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required for allauth
    'ibb_guide.middleware.HTMXRedirectMiddleware',
    'ibb_guide.middleware.SystemMonitorMiddleware',
]

ROOT_URLCONF = 'ibb_guide.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ibb_guide.context_processors.onesignal',
                'ibb_guide.context_processors.favorites',
                'management.context_processors.site_ui',
                'places.context_processors.partner_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ibb_guide.wsgi.application'

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'users.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth
]

AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Aden'
USE_I18N = True
USE_TZ = True

from django.utils.translation import gettext_lazy as _
LANGUAGES = [('ar', _('Arabic')), ('en', _('English'))]
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Caching - Removed duplicate definition (Redis config below takes precedence)
# See line 296 for production Redis cache configuration

# REST & JWT
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ),
    # Rate Limiting - Security Enhancement
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',      # Anonymous users: 100 requests/hour
        'user': '1000/hour',     # Authenticated users: 1000 requests/hour
    },
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# Third Party
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

JAZZMIN_SETTINGS = {
    "site_title": "إدارة دليل إب",
    "site_header": "لوحة تحكم دليل إب",
    "site_brand": "لوحة التحكم",
    "welcome_sign": "مرحباً بك في مركز إدارة دليل إب السياحي",
    "copyright": "دليل إب السياحي",
    "search_model": ["users.User", "places.Place"],
    "user_avatar": None,
    # Top Menu
    "topmenu_links": [
        {"name": "الرئيسية",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "عرض الموقع", "url": "/"},
        {"model": "users.User"},
        {"app": "places"},
    ],
    # User Menu
    "usermenu_links": [
        {"name": "الدعم الفني", "url": "https://github.com/ibb-guide/support", "new_window": True},
        {"model": "users.User"}
    ],
    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "management",
        "places",
        "users",
        "interactions",
        "events",
        "communities",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user-circle",
        "places.Place": "fas fa-map-marked-alt",
        "places.Category": "fas fa-tags",
        "interactions.Review": "fas fa-star",
        "management.SiteSetting": "fas fa-cogs",
        "management.HomePageSection": "fas fa-columns",
        "management.HeroSlide": "fas fa-images",
        "management.Menu": "fas fa-bars",
        "management.Footer": "fas fa-shoe-prints",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "admin/css/custom.css",
    "custom_js": "admin/js/shortcuts.js",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-success",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-success",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Auth
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

# Axes
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.25
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_VERBOSE = True

# Session
SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False  # Reduces write amplification, especially with many small HTMX/tracking requests
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Email Default
DEFAULT_FROM_EMAIL = 'دليل إب السياحي <noreply@ibb-guide.com>'

# Django Sites Framework (Required for allauth)
SITE_ID = 1

# Allauth Configuration (New format for django-allauth 65+)
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # 'mandatory', 'optional', or 'none'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False  # Security: Require POST for logout to prevent CSRF
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[دليل إب] '

# Social Account Settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # Trust Google's verified email
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_QUERY_EMAIL = True

# Google OAuth Provider Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# ==========================================
# Celery Configuration
# ==========================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Notification Provider Settings
ONESIGNAL_APP_ID = config('ONESIGNAL_APP_ID', default='')
ONESIGNAL_REST_API_KEY = config('ONESIGNAL_REST_API_KEY', default='')
FCM_SERVER_KEY = config('FCM_SERVER_KEY', default='')

# ==========================================
# File Security Configuration
# ==========================================
PRIVATE_MEDIA_ROOT = BASE_DIR / 'private_media'

# File size limits (in MB)
FILE_UPLOAD_MAX_SIZE = {
    'image': 5,
    'cover_image': 10,
    'document': 10,
    'profile_image': 2,
}

# Allowed file types
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']

# ==========================================
# Redis Cache Configuration
# ==========================================
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'KEY_PREFIX': 'ibb',
        'TIMEOUT': 300,  # Default 5 minutes
    }
}

# Session stored in Redis for horizontal scalability
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Cache TTL Constants (seconds)
CACHE_TTL_SHORT = 60       # 1 min - dynamic content
CACHE_TTL_MEDIUM = 300     # 5 min - listings
CACHE_TTL_LONG = 3600      # 1 hour - static data
CACHE_TTL_DAY = 86400      # 24 hours - rarely changing

# Ad Tracking Settings
AD_IMPRESSION_TRACKING_ENABLED = config('AD_IMPRESSION_TRACKING_ENABLED', default=True, cast=bool)
AD_TRACKING_CACHE_ALIAS = config('AD_TRACKING_CACHE_ALIAS', default='default')
AD_TRACKING_DEDUP_SECONDS = 600

# ==========================================
# ML Service (FastAPI)
# ==========================================
ML_SERVICE_URL = config('ML_SERVICE_URL', default='http://127.0.0.1:8001')
ML_SERVICE_TIMEOUT = config('ML_SERVICE_TIMEOUT', default=10, cast=int)
