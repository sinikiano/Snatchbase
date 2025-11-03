#!/bin/bash

################################################################################
# Snatchbase - Automated Installation & Deployment Script
# Version: 2.0.0
# Description: One-click installation for VPS deployment
# Usage: curl -sSL https://raw.githubusercontent.com/sinikiano/Snatchbase/main/install.sh | bash
# Or: bash install.sh
################################################################################

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SNATCHBASE_DIR="$HOME/Snatchbase"
BACKEND_DIR="$SNATCHBASE_DIR/backend"
FRONTEND_DIR="$SNATCHBASE_DIR/frontend"
LOG_FILE="$SNATCHBASE_DIR/install.log"

################################################################################
# Helper Functions
################################################################################

print_banner() {
    clear
    echo -e "${PURPLE}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ███████╗███╗   ██╗ █████╗ ████████╗ ██████╗██╗  ██╗██████╗  █████╗   ║
║   ██╔════╝████╗  ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║██╔══██╗██╔══██╗  ║
║   ███████╗██╔██╗ ██║███████║   ██║   ██║     ███████║██████╔╝███████║  ║
║   ╚════██║██║╚██╗██║██╔══██║   ██║   ██║     ██╔══██║██╔══██╗██╔══██║  ║
║   ███████║██║ ╚████║██║  ██║   ██║   ╚██████╗██║  ██║██████╔╝██║  ██║  ║
║   ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝  ║
║                                                                          ║
║              Automated Installation & Deployment Script                 ║
║                         Version 2.0.0                                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${CYAN}▶ ${1}${NC}"
    echo "▶ $1" >> "$LOG_FILE"
}

print_status() {
    echo -e "${BLUE}  [INFO]${NC} $1"
    echo "  [INFO] $1" >> "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}  [✓]${NC} $1"
    echo "  [✓] $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}  [!]${NC} $1"
    echo "  [!] $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}  [✗]${NC} $1"
    echo "  [✗] $1" >> "$LOG_FILE"
}

check_port_open() {
    local port=$1
    if command -v netstat &> /dev/null; then
        netstat -tuln | grep -q ":$port "
    elif command -v ss &> /dev/null; then
        ss -tuln | grep -q ":$port "
    else
        return 1
    fi
}

display_port_status() {
    echo -e "${YELLOW}🔌 Port Status Check:${NC}"
    
    local ports=("22:SSH" "80:HTTP" "443:HTTPS" "8000:FastAPI" "3000:React/Node" "$API_PORT:API" "5173:Frontend")
    
    for port_info in "${ports[@]}"; do
        IFS=':' read -r port name <<< "$port_info"
        if check_port_open "$port"; then
            echo -e "  ${GREEN}✓${NC} Port $port ($name) - Listening"
        else
            echo -e "  ${YELLOW}○${NC} Port $port ($name) - Not in use"
        fi
    done
    
    if [ "$DB_TYPE" = "postgresql" ]; then
        if check_port_open "5432"; then
            echo -e "  ${GREEN}✓${NC} Port 5432 (PostgreSQL) - Listening"
        else
            echo -e "  ${YELLOW}○${NC} Port 5432 (PostgreSQL) - Not in use"
        fi
    fi
    echo ""
}

ask_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    local is_secret="${4:-false}"
    
    if [ -n "$default" ]; then
        prompt="$prompt [default: $default]"
    fi
    
    echo -e "${YELLOW}❯${NC} $prompt"
    
    if [ "$is_secret" = "true" ]; then
        read -s input
        echo  # New line after secret input
    else
        read input
    fi
    
    if [ -z "$input" ] && [ -n "$default" ]; then
        input="$default"
    fi
    
    eval "$var_name='$input'"
}

confirm() {
    local prompt="$1"
    echo -e "${YELLOW}❯${NC} $prompt [y/N]"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

################################################################################
# System Requirements Check
################################################################################

check_system_requirements() {
    print_step "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "Operating System: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "Operating System: macOS"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then 
        print_warning "Running as root. Consider using a non-root user with sudo privileges."
    fi
    
    # Check available disk space (need at least 2GB)
    available_space=$(df -BG "$HOME" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 2 ]; then
        print_error "Insufficient disk space. Need at least 2GB, have ${available_space}GB"
        exit 1
    fi
    print_success "Available disk space: ${available_space}GB"
    
    # Check internet connectivity
    if ping -c 1 google.com &> /dev/null; then
        print_success "Internet connectivity: OK"
    else
        print_error "No internet connection detected"
        exit 1
    fi
}

################################################################################
# Install System Dependencies
################################################################################

install_system_dependencies() {
    print_step "Installing system dependencies..."
    
    # Detect package manager
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt-get"
        UPDATE_CMD="sudo apt-get update"
        INSTALL_CMD="sudo apt-get install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        UPDATE_CMD="sudo yum update -y"
        INSTALL_CMD="sudo yum install -y"
    elif command -v brew &> /dev/null; then
        PKG_MANAGER="brew"
        UPDATE_CMD="brew update"
        INSTALL_CMD="brew install"
    else
        print_error "No supported package manager found (apt-get, yum, or brew)"
        exit 1
    fi
    
    print_status "Package manager: $PKG_MANAGER"
    
    # Update package lists
    print_status "Updating package lists..."
    $UPDATE_CMD >> "$LOG_FILE" 2>&1
    
    # Install required packages
    REQUIRED_PACKAGES="git curl wget python3 python3-pip python3-venv build-essential sqlite3"
    
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        REQUIRED_PACKAGES="$REQUIRED_PACKAGES python3-dev"
    fi
    
    print_status "Installing required packages: $REQUIRED_PACKAGES"
    for package in $REQUIRED_PACKAGES; do
        if ! command -v "$package" &> /dev/null && ! dpkg -l | grep -q "^ii  $package"; then
            print_status "Installing $package..."
            $INSTALL_CMD "$package" >> "$LOG_FILE" 2>&1 || print_warning "Failed to install $package"
        else
            print_success "$package is already installed"
        fi
    done
    
    # Install Node.js if not present
    if ! command -v node &> /dev/null; then
        print_status "Installing Node.js..."
        if [ "$PKG_MANAGER" = "apt-get" ]; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - >> "$LOG_FILE" 2>&1
            sudo apt-get install -y nodejs >> "$LOG_FILE" 2>&1
        elif [ "$PKG_MANAGER" = "brew" ]; then
            brew install node >> "$LOG_FILE" 2>&1
        else
            print_error "Please install Node.js 18+ manually"
            exit 1
        fi
    fi
    
    print_success "Node.js version: $(node --version)"
    print_success "npm version: $(npm --version)"
    print_success "Python version: $(python3 --version)"
}

################################################################################
# Clone/Update Repository
################################################################################

setup_repository() {
    print_step "Setting up Snatchbase repository..."
    
    if [ -d "$SNATCHBASE_DIR" ]; then
        print_warning "Snatchbase directory already exists at $SNATCHBASE_DIR"
        if confirm "Do you want to update the existing installation?"; then
            cd "$SNATCHBASE_DIR"
            print_status "Pulling latest changes..."
            git pull origin main >> "$LOG_FILE" 2>&1
            print_success "Repository updated"
        else
            print_status "Using existing installation"
        fi
    else
        print_status "Cloning repository to $SNATCHBASE_DIR..."
        git clone https://github.com/sinikiano/Snatchbase.git "$SNATCHBASE_DIR" >> "$LOG_FILE" 2>&1
        print_success "Repository cloned"
    fi
    
    cd "$SNATCHBASE_DIR"
}

################################################################################
# Setup Python Environment
################################################################################

setup_python_environment() {
    print_step "Setting up Python environment..."
    
    cd "$BACKEND_DIR"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv >> "$LOG_FILE" 2>&1
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip >> "$LOG_FILE" 2>&1
    
    # Install Python dependencies
    print_status "Installing Python dependencies (this may take a few minutes)..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt >> "$LOG_FILE" 2>&1
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

################################################################################
# Setup Frontend
################################################################################

setup_frontend() {
    print_step "Setting up frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Install npm dependencies
    print_status "Installing npm dependencies (this may take a few minutes)..."
    npm install >> "$LOG_FILE" 2>&1
    print_success "Frontend dependencies installed"
    
    # Build frontend
    if confirm "Do you want to build the frontend for production?"; then
        print_status "Building frontend..."
        npm run build >> "$LOG_FILE" 2>&1
        print_success "Frontend built successfully"
    fi
}

################################################################################
# Create Directories
################################################################################

create_directories() {
    print_step "Creating necessary directories..."
    
    cd "$SNATCHBASE_DIR"
    
    mkdir -p backend/data/incoming/uploads
    mkdir -p backend/data/processed
    mkdir -p backend/logs
    
    print_success "Directories created"
}

################################################################################
# Interactive Configuration
################################################################################

configure_environment() {
    print_step "Configuring environment..."
    
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  DATABASE CONFIGURATION${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"
    
    print_status "Database options:"
    echo "  1) SQLite (recommended for testing/development)"
    echo "  2) PostgreSQL (recommended for production)"
    echo ""
    ask_input "Select database type [1-2]" DB_CHOICE "1"
    
    if [ "$DB_CHOICE" = "2" ]; then
        echo ""
        print_status "PostgreSQL Configuration:"
        ask_input "PostgreSQL host" DB_HOST "localhost"
        ask_input "PostgreSQL port" DB_PORT "5432"
        ask_input "PostgreSQL database name" DB_NAME "snatchbase"
        ask_input "PostgreSQL username" DB_USER "snatchbase"
        ask_input "PostgreSQL password" DB_PASS "" true
        
        DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    else
        DATABASE_URL="sqlite:///./snatchbase.db"
    fi
    
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  API CONFIGURATION${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"
    
    ask_input "API host (use 0.0.0.0 for external access)" API_HOST "0.0.0.0"
    ask_input "API port" API_PORT "8000"
    
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  TELEGRAM BOT CONFIGURATION (Optional)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"
    
    print_status "To enable Telegram bot:"
    echo "  1. Message @BotFather on Telegram and send /newbot"
    echo "  2. Message @userinfobot and send /start to get your user ID"
    echo ""
    
    if confirm "Do you want to configure Telegram bot now?"; then
        ask_input "Telegram bot token (from @BotFather)" TELEGRAM_BOT_TOKEN ""
        ask_input "Your Telegram user ID (from @userinfobot)" TELEGRAM_ALLOWED_USER_ID ""
        TELEGRAM_ENABLED="true"
    else
        TELEGRAM_BOT_TOKEN=""
        TELEGRAM_ALLOWED_USER_ID=""
        TELEGRAM_ENABLED="false"
    fi
    
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  BLOCKCHAIN API KEYS (Optional)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"
    
    print_status "Free API keys available from:"
    echo "  • Etherscan: https://etherscan.io/apis"
    echo "  • Polygonscan: https://polygonscan.com/apis"
    echo "  • BscScan: https://bscscan.com/apis"
    echo "  • CryptoCompare: https://www.cryptocompare.com/cryptopian/api-keys"
    echo ""
    
    if confirm "Do you want to configure blockchain API keys now?"; then
        ask_input "Etherscan API key (optional)" ETHERSCAN_API_KEY ""
        ask_input "Polygonscan API key (optional)" POLYGONSCAN_API_KEY ""
        ask_input "BscScan API key (optional)" BSCSCAN_API_KEY ""
        ask_input "CryptoCompare API key (optional)" CRYPTOCOMPARE_API_KEY ""
    else
        ETHERSCAN_API_KEY=""
        POLYGONSCAN_API_KEY=""
        BSCSCAN_API_KEY=""
        CRYPTOCOMPARE_API_KEY=""
    fi
    
    # Generate .env file
    print_step "Generating configuration files..."
    
    cat > "$BACKEND_DIR/.env" << EOF
# ============================================================================
# Snatchbase Configuration
# Generated on: $(date)
# ============================================================================

# ============================================================================
# Database Configuration
# ============================================================================
DATABASE_URL=$DATABASE_URL

# ============================================================================
# API Service Configuration
# ============================================================================
API_HOST=$API_HOST
API_PORT=$API_PORT
API_RELOAD=true
API_WORKERS=4

# ============================================================================
# Telegram Bot Service
# ============================================================================
TELEGRAM_ENABLED=$TELEGRAM_ENABLED
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_ALLOWED_USER_ID=$TELEGRAM_ALLOWED_USER_ID

# ============================================================================
# File Watcher Service
# ============================================================================
FILE_WATCHER_ENABLED=true
FILE_WATCHER_INTERVAL=5

# ============================================================================
# Wallet Balance Checker Service
# ============================================================================
WALLET_CHECKER_ENABLED=false
WALLET_CHECKER_INTERVAL=3600
WALLET_CHECK_BATCH_SIZE=100

# ============================================================================
# Blockchain API Keys
# ============================================================================
ETHERSCAN_API_KEY=$ETHERSCAN_API_KEY
POLYGONSCAN_API_KEY=$POLYGONSCAN_API_KEY
BSCSCAN_API_KEY=$BSCSCAN_API_KEY
CRYPTOCOMPARE_API_KEY=$CRYPTOCOMPARE_API_KEY

# ============================================================================
# MEGA Download Service (Optional)
# ============================================================================
MEGA_EMAIL=
MEGA_PASSWORD=
MEGA_PROXY=

# ============================================================================
# Service Management
# ============================================================================
HEALTH_CHECK_INTERVAL=30
SERVICE_RESTART_DELAY=5
MAX_RESTART_ATTEMPTS=3

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO

# ============================================================================
# Upload Directory
# ============================================================================
UPLOAD_DIR=data/incoming/uploads
EOF

    # Create frontend .env
    cat > "$FRONTEND_DIR/.env" << EOF
VITE_API_URL=http://localhost:$API_PORT
EOF

    print_success "Configuration files created"
}

################################################################################
# Initialize Database
################################################################################

initialize_database() {
    print_step "Initializing database..."
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Run database initialization
    python3 -c "from app.database import Base, engine; Base.metadata.create_all(engine)" 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        print_success "Database initialized"
    else
        print_error "Database initialization failed. Check $LOG_FILE for details"
        exit 1
    fi
}

################################################################################
# Create Systemd Services
################################################################################

create_systemd_services() {
    if ! confirm "Do you want to create systemd services for auto-start?"; then
        return
    fi
    
    print_step "Creating systemd services..."
    
    # Create backend service
    sudo tee /etc/systemd/system/snatchbase-api.service > /dev/null << EOF
[Unit]
Description=Snatchbase API Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
ExecStart=$BACKEND_DIR/venv/bin/python -m launcher.api_service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Create file watcher service
    sudo tee /etc/systemd/system/snatchbase-watcher.service > /dev/null << EOF
[Unit]
Description=Snatchbase File Watcher Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
ExecStart=$BACKEND_DIR/venv/bin/python -m launcher.file_watcher_service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable snatchbase-api.service
    sudo systemctl enable snatchbase-watcher.service
    
    print_success "Systemd services created and enabled"
    print_status "You can start services with:"
    echo "    sudo systemctl start snatchbase-api"
    echo "    sudo systemctl start snatchbase-watcher"
}

################################################################################
# Setup Nginx (Optional)
################################################################################

setup_nginx() {
    if ! confirm "Do you want to setup Nginx reverse proxy?"; then
        return
    fi
    
    print_step "Setting up Nginx..."
    
    # Install nginx
    if ! command -v nginx &> /dev/null; then
        print_status "Installing Nginx..."
        $INSTALL_CMD nginx >> "$LOG_FILE" 2>&1
    fi
    
    ask_input "Enter your domain name (or server IP)" DOMAIN_NAME "localhost"
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/snatchbase > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Frontend
    location / {
        root $FRONTEND_DIR/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:$API_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # API docs
    location /docs {
        proxy_pass http://127.0.0.1:$API_PORT/docs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/snatchbase /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    if sudo nginx -t >> "$LOG_FILE" 2>&1; then
        sudo systemctl restart nginx
        print_success "Nginx configured and started"
        print_status "Access your application at: http://$DOMAIN_NAME"
    else
        print_error "Nginx configuration test failed"
    fi
}

################################################################################
# Setup Firewall
################################################################################

setup_firewall() {
    if ! confirm "Do you want to configure firewall rules?"; then
        return
    fi
    
    print_step "Configuring firewall..."
    
    # Detect firewall system
    if command -v ufw &> /dev/null; then
        print_status "Using UFW (Uncomplicated Firewall)..."
        
        # Essential ports
        print_status "Opening essential ports..."
        sudo ufw allow 22/tcp comment 'SSH' >> "$LOG_FILE" 2>&1
        sudo ufw allow 80/tcp comment 'HTTP' >> "$LOG_FILE" 2>&1
        sudo ufw allow 443/tcp comment 'HTTPS' >> "$LOG_FILE" 2>&1
        
        # Application ports
        print_status "Opening application ports..."
        sudo ufw allow $API_PORT/tcp comment 'Snatchbase API' >> "$LOG_FILE" 2>&1
        sudo ufw allow 8000/tcp comment 'FastAPI Default' >> "$LOG_FILE" 2>&1
        sudo ufw allow 3000/tcp comment 'React/Node Apps' >> "$LOG_FILE" 2>&1
        sudo ufw allow 5173/tcp comment 'Vite Dev Server' >> "$LOG_FILE" 2>&1
        
        # Database ports (if using PostgreSQL)
        if [ "$DB_TYPE" = "postgresql" ]; then
            if confirm "Allow external PostgreSQL connections? (only if needed)"; then
                sudo ufw allow 5432/tcp comment 'PostgreSQL' >> "$LOG_FILE" 2>&1
                print_status "PostgreSQL port 5432 opened"
            fi
        fi
        
        # Display current rules
        echo ""
        print_status "Firewall rules to be applied:"
        echo "  • SSH (22/tcp) - Remote access"
        echo "  • HTTP (80/tcp) - Web traffic"
        echo "  • HTTPS (443/tcp) - Secure web traffic"
        echo "  • API ($API_PORT/tcp) - FastAPI backend"
        echo "  • Port 8000/tcp - FastAPI default port"
        echo "  • Port 3000/tcp - React/Node.js apps"
        echo "  • Vite (5173/tcp) - Frontend dev server"
        if [ "$DB_TYPE" = "postgresql" ] && sudo ufw status | grep -q "5432"; then
            echo "  • PostgreSQL (5432/tcp) - Database"
        fi
        echo ""
        
        # Enable firewall
        if confirm "Enable firewall now?"; then
            sudo ufw --force enable >> "$LOG_FILE" 2>&1
            print_success "Firewall configured and enabled"
            echo ""
            sudo ufw status numbered
        else
            print_warning "Firewall configured but not enabled. Run 'sudo ufw enable' manually."
        fi
        
    elif command -v firewall-cmd &> /dev/null; then
        print_status "Using firewalld..."
        
        # Essential ports
        print_status "Opening essential ports..."
        sudo firewall-cmd --permanent --add-service=ssh >> "$LOG_FILE" 2>&1
        sudo firewall-cmd --permanent --add-service=http >> "$LOG_FILE" 2>&1
        sudo firewall-cmd --permanent --add-service=https >> "$LOG_FILE" 2>&1
        
        # Application ports
        print_status "Opening application ports..."
        sudo firewall-cmd --permanent --add-port=$API_PORT/tcp >> "$LOG_FILE" 2>&1
        sudo firewall-cmd --permanent --add-port=8000/tcp >> "$LOG_FILE" 2>&1
        sudo firewall-cmd --permanent --add-port=3000/tcp >> "$LOG_FILE" 2>&1
        sudo firewall-cmd --permanent --add-port=5173/tcp >> "$LOG_FILE" 2>&1
        
        # Database ports
        if [ "$DB_TYPE" = "postgresql" ]; then
            if confirm "Allow external PostgreSQL connections? (only if needed)"; then
                sudo firewall-cmd --permanent --add-service=postgresql >> "$LOG_FILE" 2>&1
                print_status "PostgreSQL port opened"
            fi
        fi
        
        # Reload firewall
        sudo firewall-cmd --reload >> "$LOG_FILE" 2>&1
        print_success "Firewall configured and reloaded"
        echo ""
        sudo firewall-cmd --list-all
        
    elif command -v iptables &> /dev/null; then
        print_status "Using iptables..."
        print_warning "Setting up basic iptables rules..."
        
        # Flush existing rules (optional)
        if confirm "Flush existing iptables rules?"; then
            sudo iptables -F >> "$LOG_FILE" 2>&1
        fi
        
        # Allow established connections
        sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT >> "$LOG_FILE" 2>&1
        
        # Allow loopback
        sudo iptables -A INPUT -i lo -j ACCEPT >> "$LOG_FILE" 2>&1
        
        # Essential ports
        sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT -m comment --comment "SSH" >> "$LOG_FILE" 2>&1
        sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT -m comment --comment "HTTP" >> "$LOG_FILE" 2>&1
        sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT -m comment --comment "HTTPS" >> "$LOG_FILE" 2>&1
        
        # Application ports
        sudo iptables -A INPUT -p tcp --dport $API_PORT -j ACCEPT -m comment --comment "Snatchbase API" >> "$LOG_FILE" 2>&1
        sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT -m comment --comment "FastAPI Default" >> "$LOG_FILE" 2>&1
        sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT -m comment --comment "React/Node Apps" >> "$LOG_FILE" 2>&1
        sudo iptables -A INPUT -p tcp --dport 5173 -j ACCEPT -m comment --comment "Vite Dev" >> "$LOG_FILE" 2>&1
        
        # Database ports
        if [ "$DB_TYPE" = "postgresql" ]; then
            if confirm "Allow external PostgreSQL connections?"; then
                sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT -m comment --comment "PostgreSQL" >> "$LOG_FILE" 2>&1
            fi
        fi
        
        # Drop other incoming
        if confirm "Drop all other incoming traffic?"; then
            sudo iptables -A INPUT -j DROP >> "$LOG_FILE" 2>&1
        fi
        
        # Save rules
        if [ -f /etc/debian_version ]; then
            sudo apt-get install -y iptables-persistent >> "$LOG_FILE" 2>&1
            sudo netfilter-persistent save >> "$LOG_FILE" 2>&1
        elif [ -f /etc/redhat-release ]; then
            sudo service iptables save >> "$LOG_FILE" 2>&1
        fi
        
        print_success "Iptables rules configured"
        echo ""
        sudo iptables -L -n -v
        
    else
        print_warning "No supported firewall found (ufw, firewalld, or iptables)"
        print_warning "Please configure firewall manually with these ports:"
        echo "  • 22/tcp (SSH)"
        echo "  • 80/tcp (HTTP)"
        echo "  • 443/tcp (HTTPS)"
        echo "  • $API_PORT/tcp (API)"
        echo "  • 8000/tcp (FastAPI Default)"
        echo "  • 3000/tcp (React/Node Apps)"
        echo "  • 5173/tcp (Vite Dev)"
    fi
    
    echo ""
    print_status "Firewall Configuration Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Required Ports for Snatchbase:"
    echo "  • SSH (22)        - Remote server access"
    echo "  • HTTP (80)       - Web application (production)"
    echo "  • HTTPS (443)     - Secure web application (with SSL)"
    echo "  • API ($API_PORT)       - Backend API service"
    echo "  • Port 8000       - FastAPI default port"
    echo "  • Port 3000       - React/Node.js applications"
    echo "  • Frontend (5173) - Development server (dev only)"
    echo ""
    echo "Optional Ports:"
    echo "  • PostgreSQL (5432) - If using external database"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

################################################################################
# Final Summary
################################################################################

print_summary() {
    print_banner
    
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 INSTALLATION COMPLETE! 🎉                   ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${CYAN}📦 Installation Directory:${NC} $SNATCHBASE_DIR"
    echo -e "${CYAN}📝 Log File:${NC} $LOG_FILE"
    echo -e "${CYAN}🔧 Configuration:${NC} $BACKEND_DIR/.env"
    echo ""
    
    echo -e "${YELLOW}🚀 Quick Start Commands:${NC}"
    echo ""
    echo -e "  ${BLUE}Start Backend API:${NC}"
    echo "    cd $BACKEND_DIR"
    echo "    source venv/bin/activate"
    echo "    python -m launcher.api_service"
    echo ""
    echo -e "  ${BLUE}Start Frontend (dev):${NC}"
    echo "    cd $FRONTEND_DIR"
    echo "    npm run dev"
    echo ""
    echo -e "  ${BLUE}Start All Services (background):${NC}"
    echo "    cd $BACKEND_DIR"
    echo "    source venv/bin/activate"
    echo "    python -m launcher.all_services &"
    echo ""
    
    if [ -f "/etc/systemd/system/snatchbase-api.service" ]; then
        echo -e "${YELLOW}⚙️  Systemd Services:${NC}"
        echo "    sudo systemctl start snatchbase-api"
        echo "    sudo systemctl start snatchbase-watcher"
        echo "    sudo systemctl status snatchbase-api"
        echo ""
    fi
    
    echo -e "${YELLOW}📚 Documentation:${NC}"
    echo "    • Installation Guide: $SNATCHBASE_DIR/docs/INSTALLATION_GUIDE.md"
    echo "    • Project Structure: $SNATCHBASE_DIR/docs/PROJECT_STRUCTURE.md"
    echo "    • Configuration Audit: $SNATCHBASE_DIR/docs/CONFIGURATION_AUDIT.md"
    echo "    • Innovation Roadmap: $SNATCHBASE_DIR/docs/INNOVATION_ROADMAP.md"
    echo "    • Quick Start Guide: $SNATCHBASE_DIR/docs/QUICK_START.md"
    echo ""
    
    echo -e "${YELLOW}🌐 Access Points:${NC}"
    echo "    • API: http://localhost:$API_PORT"
    echo "    • API Docs: http://localhost:$API_PORT/docs"
    echo "    • Frontend: http://localhost:5173 (dev mode)"
    echo ""
    
    echo -e "${YELLOW}🔒 Network Ports:${NC}"
    echo "    • SSH: 22 (remote access)"
    echo "    • HTTP: 80 (web traffic)"
    echo "    • HTTPS: 443 (secure web)"
    echo "    • FastAPI: 8000 (default FastAPI port)"
    echo "    • React/Node: 3000 (default React/Node.js port)"
    echo "    • API: $API_PORT (backend service)"
    echo "    • Frontend Dev: 5173 (development only)"
    if [ "$DB_TYPE" = "postgresql" ]; then
        echo "    • PostgreSQL: 5432 (database)"
    fi
    echo ""
    
    if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
        echo -e "${GREEN}✓ Firewall (UFW) is active${NC}"
    elif command -v firewall-cmd &> /dev/null && sudo firewall-cmd --state &> /dev/null; then
        echo -e "${GREEN}✓ Firewall (firewalld) is active${NC}"
    fi
    echo ""
    
    # Display port status
    display_port_status
    
    if [ "$TELEGRAM_ENABLED" = "false" ]; then
        echo -e "${YELLOW}⚠️  Telegram Bot Not Configured${NC}"
        echo "    Edit $BACKEND_DIR/.env to add:"
        echo "    - TELEGRAM_BOT_TOKEN"
        echo "    - TELEGRAM_ALLOWED_USER_ID"
        echo ""
    fi
    
    echo -e "${GREEN}✨ Snatchbase is ready to use!${NC}\n"
    
    echo -e "${YELLOW}📌 Important Notes:${NC}"
    echo ""
    echo "  ${BLUE}Cloud Provider Firewall:${NC}"
    echo "    If you're on AWS, GCP, Azure, or DigitalOcean, you must also"
    echo "    configure security groups/firewall rules in your cloud console:"
    echo ""
    echo "    AWS EC2 Security Groups:"
    echo "      • Inbound: 22, 80, 443, 8000, 3000, $API_PORT, 5173"
    echo "      • Console: EC2 → Security Groups → Edit Inbound Rules"
    echo ""
    echo "    DigitalOcean Firewall:"
    echo "      • Inbound: 22, 80, 443, 8000, 3000, $API_PORT, 5173"
    echo "      • Console: Networking → Firewalls → Edit Rules"
    echo ""
    echo "    GCP Firewall Rules:"
    echo "      • gcloud compute firewall-rules create snatchbase \\"
    echo "        --allow tcp:22,tcp:80,tcp:443,tcp:8000,tcp:3000,tcp:$API_PORT,tcp:5173"
    echo ""
    echo "    Azure Network Security Group:"
    echo "      • Inbound: 22, 80, 443, 8000, 3000, $API_PORT, 5173"
    echo "      • Portal: NSG → Inbound security rules → Add"
    echo ""
    
    echo -e "${YELLOW}🔐 Security Recommendations:${NC}"
    echo "    • Change default SSH port from 22"
    echo "    • Setup SSL/TLS certificates (certbot for Let's Encrypt)"
    echo "    • Use strong database passwords"
    echo "    • Keep your .env file secure (chmod 600)"
    echo "    • Close port 5173 in production (dev only)"
    echo "    • Enable fail2ban for SSH protection"
    echo ""
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    # Initialize log file
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "Snatchbase Installation Log - $(date)" > "$LOG_FILE"
    
    print_banner
    
    echo -e "${CYAN}This script will install Snatchbase on your system.${NC}"
    echo -e "${CYAN}The installation process will:${NC}"
    echo "  1. Check system requirements"
    echo "  2. Install required system dependencies"
    echo "  3. Clone/update the repository"
    echo "  4. Setup Python and Node.js environments"
    echo "  5. Configure the application interactively"
    echo "  6. Initialize the database"
    echo "  7. Optionally setup systemd services and Nginx"
    echo ""
    
    if ! confirm "Do you want to continue?"; then
        echo "Installation cancelled."
        exit 0
    fi
    
    # Run installation steps
    check_system_requirements
    install_system_dependencies
    setup_repository
    create_directories
    setup_python_environment
    setup_frontend
    configure_environment
    initialize_database
    create_systemd_services
    setup_nginx
    setup_firewall
    
    # Print summary
    print_summary
    
    # Save summary to file
    print_summary > "$SNATCHBASE_DIR/INSTALLATION_SUMMARY.txt"
}

# Run main installation
main "$@"
