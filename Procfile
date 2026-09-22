release: python manage.py migrate --noinput
# SQLite runs in WAL mode, which allows readers during a write. Raise the
# worker count only after moving to Postgres via DATABASE_URL.
web: gunicorn mde.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
