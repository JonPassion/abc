# Deployment Guide for 200+ Users

## Database Setup (PostgreSQL)

### Install PostgreSQL
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### Create Database
```sql
sudo -u postgres psql
CREATE DATABASE datingsite;
CREATE USER datingsite_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE datingsite TO datingsite_user;
\q
```

### Update Settings
```python
# In datingsite/settings_production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'datingsite',
        'USER': 'datingsite_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Redis Setup

### Install Redis
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### Test Redis
```bash
redis-cli ping
```

## Environment Variables

Create `.env` file:
```bash
SECRET_KEY=your-very-long-and-random-secret-key-here
DB_NAME=datingsite
DB_USER=datingsite_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/1
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Production Deployment

### Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Install Gunicorn
```bash
pip install gunicorn
```

### Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/datingsite.service
```

Content:
```ini
[Unit]
Description=datingsite daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/justcodeit/Documents/datingsites/datingsite
EnvironmentFile=/home/justcodeit/Documents/datingsites/datingsite/.env
ExecStart=/home/justcodeit/Documents/datingsites/datingsite/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/datingsite.sock \
    datingsite.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Start Service
```bash
sudo systemctl start datingsite
sudo systemctl enable datingsite
```

## Nginx Configuration

### Install Nginx
```bash
sudo apt install nginx
```

### Create Config
```bash
sudo nano /etc/nginx/sites-available/datingsite
```

Content:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/justcodeit/Documents/datingsites/datingsite;
    }

    location /media/ {
        root /home/justcodeit/Documents/datingsites/datingsite;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/datingsite.sock;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/datingsite /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Performance Monitoring

### Monitor Database Connections
```sql
SELECT count(*) FROM pg_stat_activity;
```

### Monitor Redis
```bash
redis-cli info memory
redis-cli info stats
```

### Monitor Gunicorn Workers
```bash
sudo systemctl status datingsite
```

## Load Testing

### Install Apache Bench
```bash
sudo apt install apache2-utils
```

### Test Load
```bash
ab -n 1000 -c 50 http://yourdomain.com/api/dashboard-stats/
```

## Expected Performance

With these optimizations:
- **Concurrent Users**: 200+
- **Database Connections**: 50 max
- **Response Time**: <200ms average
- **Memory Usage**: ~2GB with 4 Gunicorn workers
- **CPU Usage**: <50% under normal load

## Scaling Further

For 500+ users:
1. Add more Gunicorn workers
2. Implement database connection pooling
3. Add CDN for static/media files
4. Consider database read replicas
5. Implement horizontal scaling with load balancer
