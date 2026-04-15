FROM apache/superset:6.0.0

USER root

ARG PYPI_MIRROR=https://pypi.org/simple/

# Instalar dependencias del sistema necesarias para chromium y clickhouse-connect
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN /app/.venv/bin/python -m ensurepip

# Instalar drivers Python:
#   - psycopg2-binary     → conexión a PostgreSQL (metadata Superset)
#   - clickhouse-connect  → driver oficial ClickHouse para Superset (SQL Interface HTTP)
#   - flask-cors          → CORS para integración con APIs externas
#   - playwright + Pillow → screenshots para Alertas & Reports
#   - gevent             → worker concurrente
#   - authlib            → OIDC/OAuth2 con Keycloak
#   - statsd             → métricas a statsd-exporter → Prometheus
RUN /app/.venv/bin/python -m pip install \
    --index-url https://pypi.org/simple/ \
    --extra-index-url $PYPI_MIRROR \
    --trusted-host $(echo $PYPI_MIRROR | awk -F[/:] '{print $4}') \
    psycopg2-binary \
    clickhouse-connect>=0.8.0 \
    flask-cors \
    playwright \
    gevent \
    Pillow \
    authlib \
    statsd

# Instalar Chromium para Playwright (necesario para PDF/screenshot de Alertas)
RUN /app/.venv/bin/playwright install-deps
RUN /app/.venv/bin/playwright install chromium

USER superset
