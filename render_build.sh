#!/bin/bash

# Render Build Script for Dating App

echo "🚀 Starting Render deployment build..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --settings=datingsite.settings_render

# Create superuser if needed (optional)
echo "👤 Creating superuser account..."
python -c "
import os
import django
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datingsite.settings_render')
django.setup()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Load sample data (optional)
echo "🎯 Loading sample data..."
python manage.py loaddata sample_data.json --settings=datingsite.settings_render 2>/dev/null || echo "No sample data file found, skipping..."

echo "✅ Build completed successfully!"
echo "🌐 App is ready to start with Gunicorn..."
