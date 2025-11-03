# Quick Start Guide - Snatchbase v2.0

## ✅ Pre-flight Checklist

Before starting, ensure:
1. Python 3.8+ is installed
2. PostgreSQL is running (for database)
3. Git is installed

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone & Setup
```bash
# Navigate to project
cd /workspaces/Snatchbase

# The project is already set up!
```

### Step 2: Configure Services
```bash
cd backend

# Create your configuration file
cp .env.template .env

# Edit .env to set your preferences
nano .env  # or use your preferred editor
```

### Step 3: Install Dependencies
```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Setup Database
```bash
# Run database setup
bash setup_db.sh
```

### Step 5: Start Services

**Option A: All services (Recommended)**
```bash
cd ..  # Back to project root
./start_snatchbase_v2.sh
```

**Option B: Individual services**
```bash
cd backend
source venv/bin/activate

# Start service manager (manages all services)
python3 launcher/service_manager.py

# OR start services individually:
python3 launcher/api_service.py
python3 launcher/file_watcher_service.py
python3 launcher/telegram_service.py  # if configured
```

**Option C: Using the CLI tool**
```bash
cd backend
source venv/bin/activate

# Start all services
python3 launcher/snatchctl.py start

# Start specific service
python3 launcher/snatchctl.py start api

# View logs
python3 launcher/snatchctl.py logs api

# Check status
python3 launcher/snatchctl.py status
```

## 🔧 Configuration Guide

Edit `backend/.env`:

```bash
# === Core Settings ===
DATABASE_URL=postgresql://snatchbase:snatchbase@localhost/snatchbase

# === API Server ===
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true         # Auto-reload on code changes (dev only)
API_WORKERS=1           # Number of worker processes

# === Services ===
FILE_WATCHER_ENABLED=true      # Auto-ingest ZIP files
TELEGRAM_ENABLED=false         # Telegram bot (requires token)
WALLET_CHECKER_ENABLED=false   # Resource intensive!

# === Telegram Bot (if enabled) ===
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_ALLOWED_USER_ID=your_id_here

# === Monitoring ===
HEALTH_CHECK_INTERVAL=30       # Seconds between health checks
SERVICE_RESTART_DELAY=5        # Seconds before restart
MAX_RESTART_ATTEMPTS=3         # Max auto-restarts

# === Logging ===
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
```

## 📊 Access Points

Once running, access:

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📝 Logs

View logs for debugging:

```bash
# All services
tail -f /tmp/snatchbase-services.log

# Individual services
tail -f backend/logs/api.log
tail -f backend/logs/file_watcher.log
tail -f backend/logs/telegram_bot.log
tail -f backend/logs/service_manager.log
```

## 🧪 Testing

Run the architecture test:

```bash
./test_architecture.sh
```

## 🛑 Stopping Services

Press `Ctrl+C` in the terminal where services are running.

Or kill specific processes:

```bash
pkill -f "service_manager.py"
pkill -f "api_service.py"
```

## ❓ Troubleshooting

### Services won't start
1. Check logs: `tail -f backend/logs/*.log`
2. Verify database is running: `sudo systemctl status postgresql`
3. Check port availability: `netstat -tulpn | grep 8000`

### Import errors
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`

### Database connection fails
1. Check DATABASE_URL in `.env`
2. Verify PostgreSQL is running
3. Check database exists: `psql -l`

### Service keeps restarting
1. Check service-specific log file
2. Look for configuration errors
3. Verify dependencies are installed

## 🎓 Next Steps

1. **Production Deployment**: See `ARCHITECTURE_V2.md` for systemd setup
2. **Add Features**: Check `REFACTORING_SUMMARY.md` for extension points
3. **Monitor Performance**: Enable wallet checker if needed
4. **Telegram Integration**: Configure bot tokens in `.env`

## 📚 Documentation

- **Architecture**: `ARCHITECTURE_V2.md`
- **Refactoring Summary**: `REFACTORING_SUMMARY.md`
- **Main README**: `README.md`

## 🆘 Get Help

1. Check logs first
2. Review documentation
3. Open GitHub issue with:
   - Service logs
   - Configuration (sanitized)
   - Steps to reproduce

---

**You're all set! Enjoy Snatchbase v2.0! 🎉**
