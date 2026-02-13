FROM apache/superset:6.0.0

USER root
ARG PYPI_MIRROR=http://mirrors.cloud.tencent.com/pypi/simple/
RUN /app/.venv/bin/python -m ensurepip
RUN /app/.venv/bin/python -m pip install --index-url $PYPI_MIRROR --trusted-host $(echo $PYPI_MIRROR | awk -F[/:] '{print $4}') psycopg2-binary flask-cors playwright gevent Pillow authlib statsd
RUN /app/.venv/bin/playwright install-deps
RUN /app/.venv/bin/playwright install chromium

USER superset
