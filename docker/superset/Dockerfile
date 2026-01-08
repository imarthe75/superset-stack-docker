FROM apache/superset:6.0.0

USER root
RUN /app/.venv/bin/python -m ensurepip
RUN /app/.venv/bin/python -m pip install psycopg2-binary flask-cors playwright gevent Pillow authlib
RUN /app/.venv/bin/playwright install-deps
RUN /app/.venv/bin/playwright install chromium

USER superset
