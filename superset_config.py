
import os
from flask_appbuilder.security.manager import AUTH_OID, AUTH_REMOTE_USER, AUTH_DB, AUTH_LDAP, AUTH_OAUTH
from celery.schedules import crontab
from flask_caching.backends.rediscache import RedisCache 

# --- Configuración de Red/Docker ---
VALKEY_HOST = "valkey" # Nombre del servicio en Docker Compose
VALKEY_PORT = 6379
POSTGRES_HOST = "postgres" # Nombre del servicio en Docker Compose
POSTGRES_PORT = 5432

# --- Configuración General de Superset ---
ROW_LIMIT = 5000000
SUPERSET_WEBSERVER_PORT = 8088

# SECRET KEY
SECRET_KEY = os.environ.get('SECRET_KEY', 'SUPER_SECRETO_CAMBIAR_ESTO_EN_PROD')

# Conexión a Base de Datos de Metadatos (Postgres)
SQLALCHEMY_DATABASE_URI = f'postgresql://superset:superset@{POSTGRES_HOST}:{POSTGRES_PORT}/superset'

# Configuración de Seguridad
WTF_CSRF_ENABLED = False 
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
ENABLE_PROXY_FIX = True
TALISMAN_ENABLED = True
ALLOW_ADHOC_SUBQUERY = True

# Content Security Policy (CSP)
TALISMAN_CONFIG = {
    "content_security_policy": {
        "default-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "img-src": ["'self'", "data:", "blob:", "https://*"],
        "worker-src": ["'self'", "blob:"],
        "connect-src": ["'self'", "https://api.mapbox.com", "https://events.mapbox.com"],
    },
    "force_https": False,
    "session_cookie_secure": False,
}

# Rate Limiting (usando Valkey)
RATELIMIT_STORAGE_URI = f"redis://{VALKEY_HOST}:{VALKEY_PORT}/3"
RATELIMIT_STRATEGY = "fixed-window"
RATELIMIT_DEFAULT = "100 per second"

# Roles y Permisos
PUBLIC_ROLE_LIKE_GAMMA = True
AUTH_ROLE_PUBLIC = 'Public'
GUEST_ROLE_NAME = "Gamma"

# Localización
BABEL_DEFAULT_LOCALE = "es"
LANGUAGES = {
    'en': {'flag': 'us', 'name': 'English'}, 
    "es": {"flag": "es", "name": "Spanish"}
}

# Mapbox
MAPBOX_API_KEY = os.environ.get('MAPBOX_API_KEY', '')

# Mapbox
MAPBOX_API_KEY = os.environ.get('MAPBOX_API_KEY', '')

# --- Authentication (Database Default / Keycloak Optional) ---
# Para activar Keycloak, cambiar AUTH_TYPE a AUTH_OID
AUTH_TYPE = AUTH_DB

# Configuración OIDC para Keycloak (Si se activa AUTH_OID)
OIDC_CLIENT_SECRETS = '/app/pythonpath/client_secret.json' # o definir params inline
OIDC_OPENID_REALM = 'superset'
OIDC_VALID_ISSUERS = 'http://host.docker.internal:8001/realms/superset'
OIDC_CLIENT_ID = 'superset'
# Nota: En producción, usar variables de entorno para secretos
OIDC_CLIENT_SECRET = os.environ.get('OIDC_CLIENT_SECRET', 'test-secret')

# Registration
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public" 

# Backend para resultados de SQL Lab
RESULTS_BACKEND = RedisCache(
    host=VALKEY_HOST, port=VALKEY_PORT, key_prefix='superset_results')

# Caches Principales
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_cache_',
    'CACHE_REDIS_URL': f'redis://{VALKEY_HOST}:{VALKEY_PORT}/0'
}
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_',
    'CACHE_REDIS_URL': f'redis://{VALKEY_HOST}:{VALKEY_PORT}/1'
}
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_URL': f'redis://{VALKEY_HOST}:{VALKEY_PORT}/2'
}

# --- Feature Flags ---
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "ENABLE_SCHEDULED_EMAIL_REPORTS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "NATIVE_FILTER_BACKEND_CACHE": True,
    "EMBEDDED_SUPERSET": True,
    "LIST_VIEWS_ONLY_CHANGE_OWNER": True,
    "EMBED_CODE_VIEW": True,
    "ENABLE_BROWSING_API": True,
    "EMAIL_NOTIFICATIONS": True,
    "ALERT_REPORT_SLACK_V2": True,
}

# Rendimiento
FORCE_DATABASE_DRIVER_CACHE_ENGINE = True
RESULTS_BACKEND_USE_MSGPACK = False

# --- CORS ---
ENABLE_CORS = True
CORS_OPTIONS = {
  'supports_credentials': True,
  'allow_headers': ['*'],
  'resources':['*'],
  'origins':['*'] 
}

# --- Celery Configuration (Reports/Alerts) ---
class CeleryConfig:
    broker_url = f"redis://{VALKEY_HOST}:{VALKEY_PORT}/0"
    result_backend = f"redis://{VALKEY_HOST}:{VALKEY_PORT}/0"
    imports = ("superset.sql_lab", "superset.tasks.scheduler")
    worker_prefetch_multiplier = 10
    task_acks_late = True
    beat_schedule = {
       "reports.scheduler": {"task": "reports.scheduler", "schedule": crontab(minute="*", hour="*")},
       "reports.prune_log": {"task": "reports.prune_log", "schedule": crontab(minute=0, hour=0)},
    }
    timezone = "America/Mexico_City"
    enable_utc = False

CELERY_CONFIG = CeleryConfig

# --- Playwright (Screenshots) ---
WEBDRIVER_TYPE = "playwright"
WEBDRIVER_OPTION_ARGS = [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--window-size=1920,1080",
]
# En Docker, el worker accede al webserver por su nombre de servicio
WEBDRIVER_BASEURL = "http://superset:8088" 
WEBDRIVER_BASEURL_USER_FRIENDLY = "http://localhost:8088"

SCREENSHOT_LOCATE_WAIT = 100
SCREENSHOT_LOAD_WAIT = 600

# --- Email Configuration ---
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = os.environ.get('SMTP_PORT', 587)
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SMTP_MAIL_FROM = SMTP_USER
SMTP_STARTTLS = True
SMTP_SSL = False
EMAIL_REPORTS_SUBJECT_PREFIX = "[Superset] "
