FROM apache/superset:latest

USER root
RUN /app/.venv/bin/python -m ensurepip
RUN /app/.venv/bin/python -m pip install psycopg2-binary flask-cors playwright gevent Pillow
RUN /app/.venv/bin/playwright install-deps
RUN /app/.venv/bin/playwright install chromium

USER superset
