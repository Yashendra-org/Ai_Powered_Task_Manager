# Stage 2/5: Progressive implementation
#!/usr/bin/env bash
# exit on error
set -o errexit

echo "===> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "===> Collecting static files with WhiteNoise..."
python manage.py collectstatic --no-input

