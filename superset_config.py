import os
import logging
from logging.handlers import RotatingFileHandler
from celery.schedules import crontab
from flask_caching.backends.rediscache import RedisCache
from flask_appbuilder.security.manager import AUTH_OID, AUTH_DB

################################################################################
# 1. LOGGING & MONITORING
################################################################################
# Configuración robusta de logs para diagnósticos
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
SUP_LOG_DIR = "/app/superset_home/logs" # Ruta dentro del contenedor Docker

# Aseguramos que existe el directorio de logs (Best effort)
if not os.path.exists(SUP_LOG_DIR):
    try:
        os.makedirs(SUP_LOG_DIR)
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(), # Log a stdout para Docker logs
        RotatingFileHandler(
            os.path.join(SUP_LOG_DIR, "superset.log"),
            maxBytes=10000000,
            backupCount=10,
        )
    ],
)

################################################################################
# 2. RED & INFRAESTRUCTURA (DOCKER)
################################################################################
VALKEY_HOST = "valkey"
VALKEY_PORT = 6379
POSTGRES_HOST = "postgres"
POSTGRES_PORT = 5432

# URL de la Base de Metadatos
SQLALCHEMY_DATABASE_URI = f'postgresql://superset:superset@{POSTGRES_HOST}:{POSTGRES_PORT}/superset'

# Puertos y Límites
SUPERSET_WEBSERVER_PORT = int(os.environ.get('SUPERSET_WEBSERVER_PORT', 8088))
ROW_LIMIT = int(os.environ.get('ROW_LIMIT', 5000)) # Límite alto para desarrollo/exploración

# Secret Key (Crítico para producción)
SECRET_KEY = os.environ.get('SECRET_KEY', 'SUPER_SECRETO_CAMBIAR_ESTO_EN_PROD')

################################################################################
# 3. FEATURE FLAGS
################################################################################
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,                  # Reportes y Alertas
    "ENABLE_SCHEDULED_EMAIL_REPORTS": True, # Emails programados
    "EMAIL_NOTIFICATIONS": True,            # Notificaciones por email
    "ALERT_REPORT_SLACK_V2": True,          # Soporte Slack V2
    # Dashboards & Filtros
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "NATIVE_FILTER_BACKEND_CACHE": True,
    "ENABLE_TEMPLATE_PROCESSING": True,     # Jinja templating
    # Embedding y API
    "EMBEDDED_SUPERSET": True,
    "EMBED_CODE_VIEW": True,
    "ENABLE_BROWSING_API": True,
    "ENABLE_EXPLORE_DRAG_AND_DROP": True,   # UX mejorada
    "ENABLE_ADVANCED_DATA_TYPES": True,     # Tipos de datos complejos
    "LIST_VIEWS_ONLY_CHANGE_OWNER": True,
}

################################################################################
# 4. SEGURIDAD & AUTENTICACIÓN
################################################################################
WTF_CSRF_ENABLED = False     # Relajado para Dev/API 
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
ENABLE_PROXY_FIX = True      # Necesario detrás de Nginx
TALISMAN_ENABLED = False     # Desactivado CSP estricto temporalmente (Dev)
ALLOW_ADHOC_SUBQUERY = True  # Permitir SQL libre

# Configuración CORS (Permisiva para Dev)
ENABLE_CORS = True
CORS_OPTIONS = {
  'supports_credentials': True,
  'allow_headers': ['*'],
  'resources':['*'],
  'origins':['*'] 
}

# Autenticación (DB por defecto, OIDC preparado)
AUTH_TYPE = AUTH_DB

# Roles
PUBLIC_ROLE_LIKE_GAMMA = True
AUTH_ROLE_PUBLIC = 'Public'
GUEST_ROLE_NAME = "Gamma"
AUTH_USER_REGISTRATION = True

# Keycloak OIDC (Si se activa AUTH_OID)
OIDC_CLIENT_SECRETS = '/app/pythonpath/client_secret.json'
OIDC_OPENID_REALM = os.environ.get('OIDC_OPENID_REALM', 'superset')
OIDC_VALID_ISSUERS = os.environ.get('OIDC_ISSUER_URL', 'http://host.docker.internal:8001/realms/superset')
OIDC_CLIENT_ID = os.environ.get('OIDC_CLIENT_ID', 'superset')
OIDC_CLIENT_SECRET = os.environ.get('OIDC_CLIENT_SECRET', 'test-secret')

################################################################################
# 5. CACHÉ & VALKEY (REDIS)
################################################################################
# Backend para resultados de SQL Lab
RESULTS_BACKEND = RedisCache(
    host=VALKEY_HOST, port=VALKEY_PORT, key_prefix='superset_results'
)

# Caches de Aplicación
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

# Rate Limiting
RATELIMIT_STORAGE_URI = f"redis://{VALKEY_HOST}:{VALKEY_PORT}/3"
RATELIMIT_STRATEGY = "fixed-window"
RATELIMIT_DEFAULT = "200 per minute"

# Rendimiento
FORCE_DATABASE_DRIVER_CACHE_ENGINE = True

################################################################################
# 6. CELERY DISPATCHER (Workers)
################################################################################
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

################################################################################
# 7. SCREENSHOTS & REPORTING (Playwright)
################################################################################
WEBDRIVER_TYPE = "playwright"
WEBDRIVER_OPTION_ARGS = [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--window-size=1920,1080",
    "--disable-software-rasterizer",
]

# URLs para el worker
WEBDRIVER_BASEURL = os.environ.get('WEBDRIVER_BASEURL', 'http://superset:8088') 
WEBDRIVER_BASEURL_USER_FRIENDLY = "http://localhost:8088"

SCREENSHOT_LOCATE_WAIT = 60
SCREENSHOT_LOAD_WAIT = 180

# Credenciales para reportes (Usuario sistema)
ALERT_REPORTS_WORKER_USERNAME = os.environ.get('ALERT_REPORTS_WORKER_USERNAME', 'admin')
# ALERT_REPORTS_WORKER_PASSWORD = "password" # Definir en env var idealmente

################################################################################
# 8. EMAIL (SMTP)
################################################################################
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = os.environ.get('SMTP_PORT', 587)
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SMTP_MAIL_FROM = SMTP_USER
SMTP_STARTTLS = True
SMTP_SSL = False
EMAIL_REPORTS_SUBJECT_PREFIX = "[Superset] "
EMAIL_REPORTS_CTA = "Ver en Dashboard"

################################################################################
# 9. LOCALIZACIÓN
################################################################################
BABEL_DEFAULT_LOCALE = "es"
LANGUAGES = {
    'en': {'flag': 'us', 'name': 'English'}, 
    "es": {"flag": "es", "name": "Español"}
}
