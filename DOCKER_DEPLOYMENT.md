# NSFWBOT Docker Deployment Guide

## 📋 Prerequisites

- Docker and Docker Compose installed
- Git (for cloning repository)
- Port 5000 available (or modify in docker-compose files)

## 🚀 Quick Start

### 1. Environment Setup

Create your environment file from the example:
```bash
# Copy the production environment template
cp .env.production .env

# Edit the .env file with your actual values
# nano .env  # Linux/Mac
# notepad .env  # Windows
```

### 2. Development Deployment

For development with auto-reload and debugging:
```bash
# Start the development environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the environment
docker-compose down
```

### 3. Production Deployment

For production with nginx proxy and optimizations:
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production environment
docker-compose -f docker-compose.prod.yml down
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_PASSWORD=your_secure_admin_password
SECRET_KEY=your_secure_secret_key_here

# Database
DATABASE_PATH=/app/data/bot_database.db

# API Keys
VENICE_INFERENCE_KEY=your_venice_inference_key
AI_API_KEY=your_venice_inference_key

# Financial Settings
TON_PRICE_USD=2.50
STARS_PRICE_USD=0.013

# Flask Settings
FLASK_ENV=production
FLASK_DEBUG=false

# Other Configuration
LOG_LEVEL=INFO
BACKUP_RETENTION_DAYS=7
```

### Database Persistence

The SQLite database is stored in Docker volumes:
- **Development**: `./data` directory mounted to container
- **Production**: Named volume `nsfwbot_data` for better isolation

### Log Files

Application logs are stored in:
- **Development**: `./logs` directory
- **Production**: Named volume `nsfwbot_logs`

## 🗄️ Database Management

### Backup Database

Use the provided backup scripts:

**Linux/Mac:**
```bash
chmod +x scripts/backup_db.sh
./scripts/backup_db.sh
```

**Windows PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\backup_db.ps1
```

### Restore Database

```bash
# Stop the container
docker-compose down

# Replace the database file
cp backups/bot_database_backup_YYYYMMDD_HHMMSS.db data/bot_database.db

# Start the container
docker-compose up -d
```

### Database Migration

If you need to migrate from an existing installation:

```bash
# Copy your existing database
cp /path/to/existing/bot_database.db ./data/

# Start the containers
docker-compose up -d
```

## 🔍 Monitoring & Troubleshooting

### Health Checks

The container includes health checks that verify:
- Application is responding on port 5000
- Database is accessible
- Critical services are running

### View Container Status

```bash
# Check container health
docker ps

# View detailed container info
docker inspect nsfwbot

# Check health check logs
docker inspect nsfwbot | grep -A 10 "Health"
```

### Application Logs

```bash
# Real-time logs
docker-compose logs -f nsfwbot

# Last 100 lines
docker-compose logs --tail=100 nsfwbot

# Logs for specific service
docker-compose logs nginx  # Production only
```

### Common Issues

**Container won't start:**
```bash
# Check if ports are available
netstat -tulpn | grep :5000

# Check Docker logs
docker-compose logs nsfwbot
```

**Database issues:**
```bash
# Check database file permissions
docker exec nsfwbot ls -la /app/data/

# Check database integrity
docker exec nsfwbot sqlite3 /app/data/bot_database.db "PRAGMA integrity_check;"
```

**Memory issues:**
```bash
# Check container resource usage
docker stats nsfwbot

# Check available system resources
docker system df
```

## 🔒 Security Considerations

### Production Security

1. **Environment Variables**: Never commit `.env` files to version control
2. **Database Access**: SQLite database is only accessible within the container
3. **Network**: Production setup uses nginx proxy for additional security
4. **User Permissions**: Container runs as non-root user
5. **Secret Management**: Use Docker secrets for sensitive data in production

### SSL/TLS Setup

For production HTTPS, configure nginx with SSL certificates:

1. Obtain SSL certificates (Let's Encrypt recommended)
2. Mount certificates in nginx container
3. Update nginx configuration for HTTPS redirect

## 📊 Scaling & Performance

### Resource Limits

Production configuration includes:
- Memory limit: 512MB
- CPU limit: 0.5 cores
- Automatic restart on failure

### Horizontal Scaling

For multiple instances:
1. Use external database (PostgreSQL recommended)
2. Implement session storage (Redis)
3. Configure load balancer
4. Share file storage between instances

## 🔄 Updates & Maintenance

### Application Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Maintenance

```bash
# Vacuum database (reclaim space)
docker exec nsfwbot sqlite3 /app/data/bot_database.db "VACUUM;"

# Analyze database (update statistics)
docker exec nsfwbot sqlite3 /app/data/bot_database.db "ANALYZE;"
```

### Log Rotation

Implement log rotation to prevent disk space issues:
```bash
# Add to crontab for automatic cleanup
0 2 * * * docker exec nsfwbot find /app/logs -name "*.log" -mtime +30 -delete
```

## 🆘 Support & Documentation

### Getting Help

1. Check container logs first
2. Verify environment configuration
3. Test database connectivity
4. Review health check status

### Useful Commands

```bash
# Interactive shell access
docker exec -it nsfwbot /bin/bash

# Database shell access
docker exec -it nsfwbot sqlite3 /app/data/bot_database.db

# Copy files from container
docker cp nsfwbot:/app/logs/bot.log ./local_bot.log

# Container resource usage
docker exec nsfwbot top
```

### Performance Monitoring

```bash
# Monitor container performance
docker stats --no-stream nsfwbot

# Check disk usage
docker exec nsfwbot df -h

# Memory usage breakdown
docker exec nsfwbot free -h
```