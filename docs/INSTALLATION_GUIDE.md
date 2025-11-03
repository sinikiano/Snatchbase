# 🚀 Snatchbase - One-Click Installation Guide

## Quick Install (VPS Deployment)

### Method 1: Direct Download & Install
```bash
curl -sSL https://raw.githubusercontent.com/sinikiano/Snatchbase/main/install.sh | bash
```

### Method 2: Clone & Install
```bash
git clone https://github.com/sinikiano/Snatchbase.git
cd Snatchbase
bash install.sh
```

---

## What the Installer Does

The automated installation script (`install.sh`) handles everything needed to deploy Snatchbase on a fresh VPS:

### 1. **System Requirements Check** ✅
- Verifies operating system (Linux/macOS)
- Checks available disk space (minimum 2GB)
- Tests internet connectivity
- Validates system resources

### 2. **Dependency Installation** 📦
Automatically installs:
- **Python 3.11+** (with pip, venv, and development tools)
- **Node.js 18+** (with npm)
- **Git** (for version control)
- **SQLite3** (default database)
- **Build tools** (gcc, make, python3-dev)
- **System utilities** (curl, wget)

### 3. **Repository Setup** 🔄
- Clones the Snatchbase repository
- Updates existing installation if already present
- Sets up proper directory structure

### 4. **Python Environment** 🐍
- Creates isolated virtual environment
- Installs all Python dependencies from `requirements.txt`
- Upgrades pip to latest version

### 5. **Frontend Setup** 🎨
- Installs all npm dependencies
- Optionally builds production assets
- Configures Vite development server

### 6. **Interactive Configuration** ⚙️
The installer will prompt you for:

#### Database Configuration
```
Choose between:
1. SQLite (recommended for development/testing)
2. PostgreSQL (recommended for production)

If PostgreSQL:
- Host (default: localhost)
- Port (default: 5432)
- Database name
- Username
- Password
```

#### API Configuration
```
- API host (default: 0.0.0.0 for external access)
- API port (default: 8000)
```

#### Telegram Bot Setup (Optional)
```
- Bot token from @BotFather
- Your user ID from @userinfobot
- Enable/disable bot service
```

#### Blockchain API Keys (Optional)
```
- Etherscan API key (free at etherscan.io/apis)
- Polygonscan API key (free at polygonscan.com/apis)
- BscScan API key (free at bscscan.com/apis)
- CryptoCompare API key (free at cryptocompare.com)
```

### 7. **Automatic .env Generation** 📝
Creates complete configuration files:
- `backend/.env` - Backend configuration
- `frontend/.env` - Frontend configuration

Example generated `.env`:
```bash
# Database
DATABASE_URL=sqlite:///./snatchbase.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# Telegram
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_ALLOWED_USER_ID=123456789

# Blockchain APIs
ETHERSCAN_API_KEY=your_key_here
# ... and more
```

### 8. **Database Initialization** 🗄️
- Creates all required database tables
- Initializes schema
- Validates database connectivity

### 9. **Systemd Service Setup** (Optional) 🔧
Creates auto-start services:

**snatchbase-api.service**
```ini
[Unit]
Description=Snatchbase API Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python -m launcher.api_service
Restart=always

[Install]
WantedBy=multi-user.target
```

**snatchbase-watcher.service**
```ini
[Unit]
Description=Snatchbase File Watcher Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python -m launcher.file_watcher_service
Restart=always

[Install]
WantedBy=multi-user.target
```

### 10. **Nginx Reverse Proxy** (Optional) 🌐
Configures Nginx for:
- Frontend serving (static files)
- API proxy (port 8000 → /api)
- API documentation (/docs)
- Custom domain support

Example Nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        # ... proxy settings
    }
}
```

### 11. **Firewall Configuration** (Optional) 🔒
Sets up UFW firewall rules:
- Port 22 (SSH) - ✅ Allowed
- Port 80 (HTTP) - ✅ Allowed
- Port 443 (HTTPS) - ✅ Allowed
- Port 8000 (API) - ✅ Allowed

---

## Installation Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    INSTALLATION START                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 1: System Requirements Check                          │
│  • OS verification                                           │
│  • Disk space check                                          │
│  • Internet connectivity test                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Install System Dependencies                        │
│  • Detect package manager (apt/yum/brew)                     │
│  • Install Python 3.11+                                      │
│  • Install Node.js 18+                                       │
│  • Install build tools                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Setup Repository                                   │
│  • Clone from GitHub                                         │
│  • Create directory structure                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Setup Python Environment                           │
│  • Create virtual environment                                │
│  • Install Python packages                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Setup Frontend                                     │
│  • Install npm packages                                      │
│  • Build production assets (optional)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Interactive Configuration                          │
│  🔹 Database setup (SQLite/PostgreSQL)                       │
│  🔹 API configuration                                        │
│  🔹 Telegram bot setup                                       │
│  🔹 Blockchain API keys                                      │
│  • Generate .env files                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 7: Initialize Database                                │
│  • Create database tables                                    │
│  • Run migrations                                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 8: Create Systemd Services (Optional)                 │
│  • snatchbase-api.service                                    │
│  • snatchbase-watcher.service                                │
│  • Enable auto-start on boot                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 9: Setup Nginx (Optional)                             │
│  • Configure reverse proxy                                   │
│  • Setup domain/SSL                                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 10: Configure Firewall (Optional)                     │
│  • Setup UFW rules                                           │
│  • Enable firewall                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               ✅ INSTALLATION COMPLETE!                      │
│                                                              │
│  📦 All services configured                                  │
│  🚀 Ready to start!                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## After Installation

### Quick Start Commands

#### Start Backend API
```bash
cd ~/Snatchbase/backend
source venv/bin/activate
python -m launcher.api_service
```

#### Start Frontend (Development)
```bash
cd ~/Snatchbase/frontend
npm run dev
```

#### Start All Services (Background)
```bash
cd ~/Snatchbase/backend
source venv/bin/activate
python -m launcher.all_services &
```

### Using Systemd Services

If you enabled systemd services during installation:

```bash
# Start services
sudo systemctl start snatchbase-api
sudo systemctl start snatchbase-watcher

# Check status
sudo systemctl status snatchbase-api
sudo systemctl status snatchbase-watcher

# View logs
sudo journalctl -u snatchbase-api -f
sudo journalctl -u snatchbase-watcher -f

# Stop services
sudo systemctl stop snatchbase-api
sudo systemctl stop snatchbase-watcher

# Restart services
sudo systemctl restart snatchbase-api
```

### Access Points

- **API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Frontend (dev):** http://localhost:5173
- **Frontend (production):** http://your-domain.com (if Nginx configured)

---

## Installation Logs & Troubleshooting

### Log Files
- **Installation Log:** `~/Snatchbase/install.log`
- **Installation Summary:** `~/Snatchbase/INSTALLATION_SUMMARY.txt`

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 2. Permission Denied
```bash
# Fix ownership
sudo chown -R $USER:$USER ~/Snatchbase

# Fix permissions
chmod +x ~/Snatchbase/install.sh
```

#### 3. Database Connection Error
```bash
# Check database configuration
cat ~/Snatchbase/backend/.env | grep DATABASE_URL

# Test SQLite
sqlite3 ~/Snatchbase/backend/snatchbase.db ".tables"

# Test PostgreSQL
psql -h localhost -U snatchbase -d snatchbase
```

#### 4. Python Dependencies Error
```bash
cd ~/Snatchbase/backend
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

#### 5. Telegram Bot Not Working
```bash
# Verify configuration
cat ~/Snatchbase/backend/.env | grep TELEGRAM

# Test bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

---

## Manual Configuration After Installation

If you skipped any optional configuration during installation, you can manually edit:

### Backend Configuration
```bash
nano ~/Snatchbase/backend/.env
```

### Frontend Configuration
```bash
nano ~/Snatchbase/frontend/.env
```

After editing, restart the services:
```bash
sudo systemctl restart snatchbase-api
```

---

## Updating Snatchbase

To update an existing installation:

```bash
cd ~/Snatchbase
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
cd ../frontend
npm install
npm run build
sudo systemctl restart snatchbase-api
```

---

## Uninstallation

To completely remove Snatchbase:

```bash
# Stop services
sudo systemctl stop snatchbase-api snatchbase-watcher
sudo systemctl disable snatchbase-api snatchbase-watcher

# Remove systemd services
sudo rm /etc/systemd/system/snatchbase-*.service
sudo systemctl daemon-reload

# Remove Nginx configuration
sudo rm /etc/nginx/sites-enabled/snatchbase
sudo rm /etc/nginx/sites-available/snatchbase
sudo systemctl restart nginx

# Remove installation
rm -rf ~/Snatchbase
```

---

## Security Recommendations

### 1. Change Default Credentials
```bash
# Generate secure password
openssl rand -base64 32

# Update .env file
nano ~/Snatchbase/backend/.env
```

### 2. Enable HTTPS (SSL/TLS)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 3. Firewall Configuration
```bash
# Enable UFW
sudo ufw enable

# Check status
sudo ufw status
```

### 4. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Snatchbase
cd ~/Snatchbase && git pull
```

---

## Support & Documentation

- **Project Documentation:** `~/Snatchbase/README.md`
- **Configuration Guide:** `~/Snatchbase/CONFIGURATION_AUDIT.md`
- **API Documentation:** http://localhost:8000/docs
- **Innovation Roadmap:** `~/Snatchbase/INNOVATION_ROADMAP.md`

---

**Installation script features:**
✅ Fully automated installation
✅ Interactive configuration wizard
✅ Automatic dependency resolution
✅ Database initialization
✅ Systemd service creation
✅ Nginx reverse proxy setup
✅ Firewall configuration
✅ Comprehensive error logging
✅ Installation summary report

**One command to deploy everything!** 🚀
