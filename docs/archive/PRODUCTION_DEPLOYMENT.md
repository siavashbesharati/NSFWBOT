# 🚀 NSFWBot Production Deployment Guide

## Windows Server 2019 Setup

This guide will help you deploy NSFWBot as a reliable production service on Windows Server 2019.

## 📋 Prerequisites

1. **Python 3.8+** installed and in PATH
2. **NSSM (Non-Sucking Service Manager)** installed
   - Download: https://nssm.cc/download
   - Add to PATH or place in a directory in PATH
3. **All Python dependencies** installed (`pip install -r requirements.txt`)
4. **Bot configured** with `python config_manager.py --setup`

## 🔧 Production Optimizations Applied

### ✅ Auto-Restart System
- Bot automatically restarts on crashes (up to 10 attempts)
- 30-second delay between restart attempts
- Memory monitoring and cleanup

### ✅ Database Optimizations
- WAL (Write-Ahead Logging) mode enabled
- Connection pooling (5 connections)
- 30-second timeouts
- Optimized cache settings

### ✅ Health Monitoring
- `/health` endpoint for monitoring
- System resource tracking
- Database connectivity checks

### ✅ Improved Polling
- 1-second poll intervals
- 30-second timeouts
- Automatic pending update cleanup

## 🚀 Deployment Steps

### Step 1: Install NSSM
```powershell
# Download NSSM and extract to C:\nssm\
# Add C:\nssm\ to your system PATH
```

### Step 2: Run Service Setup
```powershell
# Using PowerShell (recommended)
.\setup_windows_service.ps1

# Or using batch file
setup_windows_service.bat
```

### Step 3: Verify Installation
```powershell
# Check service status
nssm status NSFWBot

# View service logs
type logs\service_stdout.log
type logs\service_stderr.log
```

## 📊 Monitoring & Management

### Service Commands
```powershell
# Start service
nssm start NSFWBot

# Stop service
nssm stop NSFWBot

# Restart service
nssm restart NSFWBot

# Check status
nssm status NSFWBot

# Edit configuration
nssm edit NSFWBot

# Remove service
nssm remove NSFWBot confirm
```

### Health Check
```
http://your-server-ip:4656/health
```

Returns JSON with:
- Service status
- Memory usage
- CPU usage
- Database health
- User/message counts

### Log Files
- `logs/service_stdout.log` - Standard output
- `logs/service_stderr.log` - Error logs

## 🔍 Troubleshooting

### Service Won't Start
1. Check Python installation: `python --version`
2. Check bot configuration: `python config_manager.py --setup`
3. Check dependencies: `pip install -r requirements.txt`
4. Check logs: `type logs\service_stderr.log`

### Bot Becomes Unresponsive
1. Check health endpoint: `curl http://localhost:4656/health`
2. Check service status: `nssm status NSFWBot`
3. Restart service: `nssm restart NSFWBot`
4. Check logs for errors

### High Memory Usage
- Service automatically monitors memory
- Restarts if usage exceeds 800MB
- Check logs for memory warnings

### Database Issues
- Automatic connection pooling
- WAL mode prevents corruption
- 30-second timeouts prevent hanging

## 🔒 Security Considerations

1. **Firewall**: Open only port 4656 inbound
2. **Admin Access**: Change default admin password
3. **IP Restrictions**: Consider restricting dashboard access to your IP
4. **Updates**: Keep Python and dependencies updated

## 📈 Performance Tuning

### For High Traffic (100+ users):
```powershell
# Edit service configuration
nssm edit NSFWBot

# Increase memory limits if needed
# Adjust restart delays
```

### Database Optimization:
- WAL mode is already enabled
- Consider moving to external PostgreSQL for 1000+ users
- Regular backup of `bot_database.db`

## 🔄 Updates & Maintenance

### Updating the Bot:
1. Stop service: `nssm stop NSFWBot`
2. Update code from repository
3. Install new dependencies: `pip install -r requirements.txt`
4. Start service: `nssm start NSFWBot`

### Backup Strategy:
```powershell
# Stop service before backup
nssm stop NSFWBot

# Backup database
copy bot_database.db backup\bot_database_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db

# Start service
nssm start NSFWBot
```

## 📞 Support

If issues persist:
1. Check all log files
2. Verify firewall settings
3. Test health endpoint
4. Check Windows Event Viewer
5. Ensure NSSM is properly installed

## ✅ Success Checklist

- [ ] NSSM installed and in PATH
- [ ] Python 3.8+ installed
- [ ] Bot configured with valid tokens
- [ ] Service installed: `nssm status NSFWBot` shows RUNNING
- [ ] Dashboard accessible: `http://your-ip:4656`
- [ ] Health endpoint working: `http://your-ip:4656/health`
- [ ] Bot responding to Telegram messages
- [ ] Logs show no critical errors

---

**🎉 Your bot is now running as a production-grade Windows service!**