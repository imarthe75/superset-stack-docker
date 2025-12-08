FROM apache/superset:latest

USER root
RUN pip install --target /app/.venv/lib/python3.10/site-packages psycopg2-binary flask-cors playwright gevent Pillow
RUN playwright install-deps
RUN playwright install chromium

USER superset
