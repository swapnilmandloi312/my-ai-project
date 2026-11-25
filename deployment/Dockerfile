FROM python:3.13-slim@sha256:7249d5587b78209a006dc4a3b5340678f84ea729239193aa559962cd8c1fce50
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY deployment/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes --no-deps -r requirements.txt && pip check && groupadd -g 10001 app && useradd -u 10001 -g app -M -s /usr/sbin/nologin app && mkdir /data && chown app:app /data
COPY secure_service /app/secure_service
COPY deployment/seed_staging.py deployment/backup.py /app/deployment/
USER 10001:10001
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "2", "--timeout", "15", "--graceful-timeout", "15", "--preload", "secure_service.http:from_env()"]
