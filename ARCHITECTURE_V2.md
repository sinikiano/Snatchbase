# Snatchbase v2.0 - Modular Architecture

## 🎯 Overview

Snatchbase v2.0 introduces a modular, service-oriented architecture that improves reliability, maintainability, and prevents cascade failures.

## 🏗️ Architecture Changes

### Before (v1.0)
- Single monolithic `main.py` (490+ lines)
- All services run in the same process
- One failure crashes everything
- Hard to debug and maintain

### After (v2.0)
- **Modular routers**: Credentials, Devices, Statistics, Files
- **Independent services**: Each service runs in its own process
- **Service manager**: Monitors health and auto-restarts failed services
- **Configuration system**: Enable/disable features via `.env`

## 📁 New Structure

```
backend/
├── launcher/                    # Service management
│   ├── config.py               # Central configuration
│   ├── service_manager.py      # Process supervisor with health checks
│   ├── api_service.py          # FastAPI server launcher
│   ├── telegram_service.py     # Telegram bot launcher
│   ├── file_watcher_service.py # ZIP ingestion launcher
│   └── wallet_checker_service.py # Wallet balance checker
├── app/
│   ├── main.py                 # Simplified FastAPI app (58 lines!)
│   ├── routers/                # Modular route handlers
│   │   ├── credentials.py      # Credential search & export
│   │   ├── devices.py          # Device management
│   │   ├── statistics.py       # Analytics endpoints
│   │   ├── files.py            # File & system search
│   │   └── wallets.py          # Wallet operations (existing)
│   └── services/               # Business logic (unchanged)
├── logs/                       # Individual service logs
└── .env                        # Service configuration
```

## 🚀 Quick Start

### 1. Configure Services

```bash
cd backend
cp .env.template .env
# Edit .env to configure services
```

### 2. Start All Services

```bash
./start_snatchbase_v2.sh
```

Or use the original script (still works):

```bash
./start_snatchbase.sh
```

### 3. Start Individual Services (Advanced)

```bash
cd backend
source venv/bin/activate

# Start only the API
python3 launcher/api_service.py

# Start only the file watcher
python3 launcher/file_watcher_service.py

# Start only the Telegram bot
python3 launcher/telegram_service.py

# Start all with monitoring
python3 launcher/service_manager.py
```

## ⚙️ Configuration

Edit `backend/.env` to enable/disable services:

```bash
# Enable/disable specific services
API_ENABLED=true              # Always required
FILE_WATCHER_ENABLED=true     # Auto-ingest ZIPs
TELEGRAM_ENABLED=true         # Telegram bot
WALLET_CHECKER_ENABLED=false  # Resource intensive

# Health monitoring
HEALTH_CHECK_INTERVAL=30      # Seconds between health checks
SERVICE_RESTART_DELAY=5       # Seconds before restart
MAX_RESTART_ATTEMPTS=3        # Max auto-restarts per service
```

## 🎯 Benefits

### 1. **No Cascade Failures**
If one service crashes, others keep running. The service manager will attempt to restart the failed service.

### 2. **Easy Debugging**
Each service has its own log file in `backend/logs/`:
- `api.log` - FastAPI server
- `telegram_bot.log` - Telegram bot
- `file_watcher.log` - ZIP ingestion
- `wallet_checker.log` - Wallet balance checks
- `service_manager.log` - Overall system health

### 3. **Better Performance**
- Services run in separate processes
- CPU/memory isolated
- Can scale individual services

### 4. **Maintainability**
- Small, focused files (< 200 lines each)
- Clear separation of concerns
- Easy to find and fix bugs

### 5. **Flexibility**
- Enable only needed services
- Easy to add new services
- Simple to test components independently

## 📊 Service Manager Features

The service manager (`launcher/service_manager.py`) provides:

- **Auto-restart**: Failed services automatically restart
- **Health checks**: HTTP health checks for API, process checks for others
- **Restart limits**: Prevents infinite restart loops
- **Graceful shutdown**: Clean shutdown on Ctrl+C
- **Status logging**: Detailed logs of all service events

## 🔍 Monitoring

### View All Service Logs
```bash
tail -f /tmp/snatchbase-services.log
```

### View Individual Service Logs
```bash
tail -f backend/logs/api.log
tail -f backend/logs/telegram_bot.log
tail -f backend/logs/file_watcher.log
```

### Check Service Status
```bash
# Check if services are running
ps aux | grep "launcher"

# Check API health
curl http://localhost:8000/health
```

## 🐛 Troubleshooting

### Service Won't Start
1. Check logs in `backend/logs/`
2. Verify configuration in `.env`
3. Ensure dependencies are installed

### Service Keeps Restarting
1. Check for configuration errors
2. Review service-specific logs
3. Verify database connection
4. Check for port conflicts

### API Returns Errors
1. Check `backend/logs/api.log`
2. Verify database is running
3. Check for missing migrations

## 🔄 Migration from v1.0

The old architecture still works! Both start scripts are available:

- `start_snatchbase.sh` - Original (works as before)
- `start_snatchbase_v2.sh` - New modular architecture

To migrate:
1. Copy `.env.template` to `.env`
2. Configure your services
3. Use `start_snatchbase_v2.sh`

## 📝 Next Steps

Potential improvements:
- [ ] Docker compose for easier deployment
- [ ] Systemd service files for production
- [ ] Metrics endpoint (Prometheus)
- [ ] Service dashboard UI
- [ ] Load balancing for API
- [ ] Database connection pooling per service

## 🤝 Contributing

When adding new features:
1. Create a new router in `app/routers/` if adding API endpoints
2. Create a new service launcher in `launcher/` if adding a background service
3. Register the service in `launcher/service_manager.py`
4. Add configuration options to `launcher/config.py`
5. Update `.env.template` with new options

## 📞 Support

- File bugs in GitHub Issues
- Check logs first: `tail -f backend/logs/*.log`
- Include service manager log when reporting issues
