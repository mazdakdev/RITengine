#!/bin/sh
echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Generating default prompts..."
python manage.py create_prompts

exec "$@"