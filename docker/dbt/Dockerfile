FROM python:3.11-slim

WORKDIR /dbt_aura

# Instalar dbt-clickhouse y dependencias de calidad
RUN pip install --no-cache-dir \
    dbt-clickhouse>=1.8.0 \
    dbt-core>=1.8.0 \
    great-expectations>=1.0.0 \
    clickhouse-driver>=0.2.9

# Copiar proyecto dbt
COPY . /dbt_aura

# Instalar dependencias dbt (packages.yml si existe)
RUN dbt deps --project-dir /dbt_aura --profiles-dir /dbt_aura || true

# Entrypoint por defecto — Prefect puede sobreescribir el CMD
ENTRYPOINT ["dbt"]
CMD ["run", "--project-dir", "/dbt_aura", "--profiles-dir", "/dbt_aura"]
