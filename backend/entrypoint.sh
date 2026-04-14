#!/bin/sh
set -e

echo "Waiting for database..."
while ! python -c "
import psycopg2, os
psycopg2.connect(
  dbname=os.environ['DB_NAME'],
  user=os.environ['DB_USER'],
  password=os.environ['DB_PASSWORD'],
  host=os.environ['DB_HOST'],
  port=os.environ['DB_PORT']
)
" 2>/dev/null; do
  sleep 1
done
echo "Database ready."

# Only the backend container runs setup (migrate, collectstatic, seed).
# Workers skip this to avoid concurrent migration race conditions.
if [ "$RUN_SETUP" = "true" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput --clear
  python manage.py seed_permissions
fi

exec "$@"
