# Deployment Guide

This document covers deploying HireMind to production environments.

## Pre-Deployment Checklist

- [ ] Code reviewed and merged to main branch
- [ ] All tests passing (`pytest` and `npm test`)
- [ ] Environment variables documented
- [ ] Database migrations completed
- [ ] Security audit completed
- [ ] Performance tested
- [ ] Documentation updated
- [ ] Version bumped in package.json

## Environment Considerations

### Local Development
```bash
DEBUG=true
DATABASE_URL=sqlite:///./database/hiremind.db
EMBEDDING_DEVICE=cpu
```

### Staging
```bash
DEBUG=false
DATABASE_URL=postgresql://user:password@staging-db:5432/hiremind
EMBEDDING_DEVICE=cuda  # If GPU available
SECRET_KEY=staging-secret-key-here
```

### Production
```bash
DEBUG=false
DATABASE_URL=postgresql://user:password@prod-db:5432/hiremind
EMBEDDING_DEVICE=cuda  # Recommended for production
SECRET_KEY=production-secret-key-here
CORS_ORIGINS=https://app.hiremind.ai
```

## Backend Deployment

### Option 1: Traditional Server (Ubuntu/Debian)

#### 1. Setup Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.9 python3-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create app directory
sudo mkdir -p /var/www/hiremind
sudo chown $USER:$USER /var/www/hiremind
```

#### 2. Deploy Application

```bash
cd /var/www/hiremind
git clone https://github.com/yourusername/HireMind.git app
cd app

# Setup Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
pip install gunicorn

# Setup environment
cp .env.example .env
# Edit .env with production values
```

#### 3. Setup Database

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE hiremind_db;
CREATE USER hiremind_user WITH PASSWORD 'strong_password';
ALTER ROLE hiremind_user SET client_encoding TO 'utf8';
ALTER ROLE hiremind_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE hiremind_user SET default_transaction_deferrable TO on;
ALTER ROLE hiremind_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hiremind_db TO hiremind_user;
\q

# Initialize database
python database/init_db.py
```

#### 4. Setup Systemd Service

Create `/etc/systemd/system/hiremind-api.service`:

```ini
[Unit]
Description=HireMind API Server
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/hiremind/app
Environment="PATH=/var/www/hiremind/app/venv/bin"
ExecStart=/var/www/hiremind/app/venv/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:8000 \
    backend.app.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hiremind-api
sudo systemctl start hiremind-api
```

#### 5. Setup Nginx Reverse Proxy

Create `/etc/nginx/sites-available/hiremind`:

```nginx
server {
    listen 80;
    server_name api.hiremind.app;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.hiremind.app;
    
    ssl_certificate /etc/letsencrypt/live/api.hiremind.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.hiremind.app/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/hiremind /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d api.hiremind.app
```

### Option 2: Docker Deployment

Create `Dockerfile.backend`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Option 3: Cloud Platforms

#### Heroku
```bash
heroku login
heroku create hiremind-api
heroku addons:create heroku-postgresql:standard-0
git push heroku main
```

#### AWS EC2
- Create EC2 instance
- Use deployment scripts above
- Configure RDS for PostgreSQL
- Setup ELB for load balancing

#### Railway.app
```bash
railway login
railway init
railway up
```

#### Render
- Connect GitHub repo
- Create PostgreSQL database
- Set environment variables
- Deploy

## Frontend Deployment

### Option 1: Static Hosting (Vercel/Netlify)

#### Vercel

```bash
npm install -g vercel
vercel
# Follow prompts
```

#### Netlify

1. Connect GitHub repository
2. Build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
3. Environment variables:
   - `VITE_API_BASE_URL`: Your API URL

### Option 2: AWS S3 + CloudFront

```bash
# Build
npm run build

# Upload to S3
aws s3 sync dist/ s3://hiremind-frontend/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Option 3: Docker + Nginx

Create `Dockerfile.frontend`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:alpine

COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Database Backup & Recovery

### PostgreSQL Backup

```bash
# Backup
pg_dump -U hiremind_user hiremind_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U hiremind_user hiremind_db < backup_YYYYMMDD.sql
```

### Automated Backups

Create backup script at `/usr/local/bin/backup-hiremind.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/hiremind"
mkdir -p $BACKUP_DIR
pg_dump -U hiremind_user hiremind_db | gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-hiremind.sh
```

## Monitoring & Logging

### Application Logs

```bash
# Check service status
sudo systemctl status hiremind-api

# View logs
sudo journalctl -u hiremind-api -f

# Log file
tail -f /var/www/hiremind/app/logs/hiremind.log
```

### Monitoring Tools

- **Sentry**: Error tracking
- **New Relic**: Performance monitoring
- **Datadog**: Infrastructure monitoring
- **ELK Stack**: Log aggregation

### Health Checks

```bash
curl http://api.hiremind.app/health
```

## Performance Optimization

### Backend
- Enable caching (Redis)
- Use connection pooling
- Optimize database queries
- Use CDN for static files

### Frontend
- Enable gzip compression
- Minify JavaScript
- Optimize images
- Use service workers

### Network
- Use CDN for content
- Enable HTTP/2
- Implement rate limiting
- Use HTTP caching headers

## Scaling Strategies

### Horizontal Scaling
- Add more backend instances
- Use load balancer (Nginx, HAProxy)
- Database replication

### Vertical Scaling
- Increase server resources
- Use GPU for embeddings
- Increase database capacity

## Disaster Recovery

### Backup Strategy
- Daily database backups
- Code version control
- Environment documentation
- Disaster recovery plan

### Recovery Procedures
1. Restore from backup
2. Verify data integrity
3. Test in staging
4. Deploy to production
5. Monitor for issues

## Post-Deployment

- [ ] Verify application running
- [ ] Check database connectivity
- [ ] Test API endpoints
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify SSL certificate
- [ ] Test email notifications
- [ ] Document deployment changes

## Support & Troubleshooting

### Common Issues

**502 Bad Gateway**
- Check backend service: `sudo systemctl status hiremind-api`
- Check Nginx configuration: `sudo nginx -t`
- View logs: `sudo journalctl -u hiremind-api -n 50`

**Database Connection Error**
- Verify PostgreSQL running: `sudo systemctl status postgresql`
- Check connection string in `.env`
- Verify database exists: `psql -U hiremind_user -l`

**High CPU Usage**
- Check active processes: `top`
- Review slow queries
- Optimize database indexes
- Scale horizontally

---

For detailed information, see:
- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)
- [Security Policy](./SECURITY.md)
