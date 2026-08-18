# Stage 4/5: Progressive implementation
#!/usr/bin/env bash
# exit on error
set -o errexit

echo "===> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "===> Collecting static files with WhiteNoise..."
python manage.py collectstatic --no-input

echo "===> Running database migrations..."
python manage.py migrate

# Optionally seed development data if enabled (default on first deploy)
if [ "$SEED_DEV_DATA" = "true" ]; then
    echo "===> Seeding demo development data and executive habits..."
    python manage.py seed_dev_data
fi

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "===> Creating superuser from environment variables..."
