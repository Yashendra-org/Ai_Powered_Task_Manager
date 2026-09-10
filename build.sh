# Stage 4/5: Authentication & deployment refinement
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

# Ensure demo student user and executive habits exist unless explicitly disabled
if [ "$SEED_DEV_DATA" != "false" ]; then
    echo "===> Ensuring demo student user and executive habits exist..."
    python manage.py seed_dev_data
fi

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "===> Creating superuser from environment variables..."
