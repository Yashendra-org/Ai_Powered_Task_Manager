# Stage 3/5: Authentication & deployment refinement
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
