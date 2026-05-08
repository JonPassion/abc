# Render.com Deployment Guide

## 🚀 Deploy Your Dating App on Render

### Prerequisites
- GitHub account with your code pushed
- Render.com account (free tier available)
- All configuration files created (see below)

## 📋 Files Created for Render Deployment

### ✅ Configuration Files
1. **`render.yaml`** - Render service configuration
2. **`settings_render.py`** - Render-specific Django settings
3. **`render_build.sh`** - Build script for Render
4. **Updated `requirements.txt`** - Added Render dependencies

### 🏗️ Services Configured

#### 1. PostgreSQL Database
- **Service**: `dating-db`
- **Plan**: Free tier
- **Auto-configured** with environment variables

#### 2. Redis Cache
- **Service**: `dating-redis`
- **Plan**: Free tier
- **Used for**: Sessions and query caching

#### 3. Django Web App
- **Service**: `dating-app`
- **Plan**: Free tier
- **Features**: Auto-deployment, SSL, custom domain

#### 4. Background Worker
- **Service**: `dating-worker`
- **Plan**: Free tier
- **Purpose**: Background tasks and notifications

## 🛠️ Deployment Steps

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Configure for Render deployment"
git push origin main
```

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Verify email

### Step 3: Connect Repository
1. Click "New Web Service"
2. Connect your GitHub repository
3. Select "Build and deploy from a GitHub repository"

### Step 4: Configure Deployment
1. **Name**: `dating-app`
2. **Environment**: Python 3
3. **Build Command**: `./render_build.sh`
4. **Start Command**: `gunicorn datingsite.wsgi:application --bind 0.0.0.0:$PORT`
5. **Environment Variables**:
   - `DJANGO_SETTINGS_MODULE`: `datingsite.settings_render`
   - `SECRET_KEY`: (auto-generated)

### Step 5: Add Database
1. Click "New PostgreSQL Database"
2. **Name**: `dating-db`
3. **Plan**: Free
4. **Database Name**: `datingsite`
5. **User**: `datingsite_user`

### Step 6: Add Redis
1. Click "New Redis Instance"
2. **Name**: `dating-redis`
3. **Plan**: Free

### Step 7: Connect Services
1. In your web service settings:
   - Add `DATABASE_URL` environment variable from PostgreSQL
   - Add `REDIS_URL` environment variable from Redis
   - Add `ALLOWED_HOSTS`: `.onrender.com`

## 🔧 Environment Variables

### Required Variables
```bash
DJANGO_SETTINGS_MODULE=datingsite.settings_render
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
ALLOWED_HOSTS=.onrender.com
DEBUG=False
```

### Optional Variables
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 🌐 Access URLs

After deployment:
- **Main App**: `https://dating-app.onrender.com`
- **Admin Panel**: `https://dating-app.onrender.com/admin`
- **API Endpoints**: `https://dating-app.onrender.com/api/`

## 📱 Mobile Access

The app is mobile-responsive and PWA-ready:
- Works on all mobile browsers
- Can be installed as mobile app
- Touch-optimized interface

## ⚡ Performance Features

### Optimized for 200+ Users
- **PostgreSQL**: Production database with indexes
- **Redis**: Caching for sessions and queries
- **Gunicorn**: Multiple worker processes
- **WhiteNoise**: Static file serving
- **Connection Pooling**: Database connection reuse

### Caching Strategy
- **Dashboard Stats**: 5 minutes cache
- **Browse Users**: 30 seconds cache
- **User Profiles**: 5 minutes cache
- **API Responses**: Various timeouts

## 🔍 Health Monitoring

### Health Check Endpoint
```
GET /health/
```

Response:
```json
{
    "status": "healthy",
    "database": "connected",
    "cache": "connected"
}
```

### Monitoring
- Render provides built-in metrics
- Check logs in Render dashboard
- Monitor response times and errors

## 🛡️ Security Features

### SSL/HTTPS
- Automatic SSL certificate
- HTTPS redirect enabled
- Secure headers configured

### Django Security
- CSRF protection enabled
- Security headers set
- Session cookies secure
- Content type protection

## 📊 Scaling Options

### Free Tier Limits
- **Web Service**: 750 hours/month
- **Database**: 256MB RAM, 90 connections
- **Redis**: 25MB memory

### Paid Plans
- **Starter**: $7/month (more RAM, connections)
- **Standard**: $25/month (better performance)
- **Pro**: Custom pricing (high traffic)

## 🔄 Auto-Deployment

### Automatic Updates
- Push to GitHub triggers rebuild
- Database migrations run automatically
- Static files collected automatically
- Zero-downtime deployments

### Manual Deployment
1. Push changes to GitHub
2. Render automatically detects changes
3. Builds and deploys new version
4. Health checks ensure successful deployment

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check DATABASE_URL format
DATABASE_URL=postgresql://username:password@host:port/database
```

#### 2. Static Files Not Loading
```bash
# Ensure STATIC_ROOT is set correctly
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

#### 3. Redis Connection Error
```bash
# Check REDIS_URL format
REDIS_URL=redis://host:port
```

#### 4. Migration Issues
```bash
# Run migrations manually
python manage.py migrate --settings=datingsite.settings_render
```

### Debug Mode
For debugging, temporarily enable:
```bash
DEBUG=True
```

## 📈 Performance Monitoring

### Key Metrics
- **Response Time**: <200ms target
- **Uptime**: 99.9%+ target
- **Database Connections**: Monitor usage
- **Memory Usage**: Keep under limits

### Optimization Tips
- Monitor cache hit rates
- Optimize database queries
- Use CDN for static files
- Enable compression

## 🎯 Next Steps

After successful deployment:

1. **Test All Features**
   - User registration/login
   - Profile browsing
   - Matching system
   - Chat functionality

2. **Monitor Performance**
   - Check response times
   - Monitor database usage
   - Review error logs

3. **Scale if Needed**
   - Upgrade to paid plans
   - Add CDN
   - Implement monitoring

4. **Custom Domain**
   - Add custom domain
   - Configure DNS
   - Update SSL certificate

Your dating app is now ready for production deployment on Render.com! 🚀
