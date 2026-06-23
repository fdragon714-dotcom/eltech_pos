#!/bin/sh
set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Check if we need to load seed data
# We check if the auth_user table is empty. If it is, we assume it's a fresh database.
echo "Checking if we need to load seed data..."
if python manage.py shell -c "from django.contrib.auth.models import User; exit(0 if User.objects.exists() else 1)"; then
    echo "Data already exists, skipping seed data loading."
else
    echo "Database is empty. Loading seed data..."
    if [ -f seed_data.json ]; then
        python manage.py loaddata seed_data.json
        echo "Seed data loaded successfully."
    else
        echo "seed_data.json not found, skipping."
    fi
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn pos.wsgi:application --bind 0.0.0.0:8000
