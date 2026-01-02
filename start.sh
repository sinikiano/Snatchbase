#!/bin/bash
################################################################################
# Snatchbase - Unified Startup Script
# Version: 3.0.0
# Description: Complete project startup - handles installation, configuration,
#              database setup, and service management
################################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$BACKEND_DIR/logs"

################################################################################
# Helper Functions
################################################################################

print_banner() {
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
║                     Unified Startup Script v3.0                         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${CYAN}▶ ${1}${NC}"
}

print_info() {
    echo -e "${BLUE}  [INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}  [✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}  [!]${NC} $1"
}

print_error() {
    echo -e "${RED}  [✗]${NC} $1"
}

################################################################################
# Installation Functions
################################################################################

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python version: $PYTHON_VERSION"
        return 0
    else
        print_error "Python3 not found. Please install Python 3.10+"
        return 1
    fi
}

check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js version: $NODE_VERSION"
        return 0
    else
        print_warning "Node.js not found. Frontend will not be available."
        return 1
    fi
}

check_archive_tools() {
    print_step "Checking archive extraction tools..."
    
    # Check for unrar
    if command -v unrar &> /dev/null; then
        print_success "unrar is installed"
    else
        print_warning "unrar not found. Install with: sudo apt install unrar"
    fi
    
    # Check for 7z
    if command -v 7z &> /dev/null; then
        print_success "7z is installed"
    else
        print_warning "7z not found. Install with: sudo apt install p7zip-full"
    fi
}

setup_backend() {
    print_step "Setting up backend..."
    cd "$BACKEND_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        print_info "Installing Python dependencies..."
        pip install -r requirements.txt --quiet
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found!"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

setup_frontend() {
    print_step "Setting up frontend..."
    cd "$FRONTEND_DIR"
    
    if [ ! -d "node_modules" ]; then
        print_info "Installing npm dependencies..."
        npm install --silent
        print_success "Frontend dependencies installed"
    else
        print_info "Frontend dependencies already installed"
    fi
    
    cd "$SCRIPT_DIR"
}

create_env_files() {
    print_step "Checking configuration files..."
    
    # Backend .env
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        if [ -f "$BACKEND_DIR/.env.example" ]; then
            print_info "Creating backend .env from example..."
            cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
            print_success "Backend .env created"
            print_warning "Please edit $BACKEND_DIR/.env with your settings"
        else
            print_warning "No .env.example found, creating minimal .env..."
            cat > "$BACKEND_DIR/.env" << 'EOF'
# Database Configuration
DATABASE_URL=sqlite:///./snatchbase.db

# API Service Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# Telegram Bot Service (disabled by default)
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_ID=

# File Watcher Service
FILE_WATCHER_ENABLED=true
FILE_WATCHER_INTERVAL=5

# Wallet Balance Checker Service
WALLET_CHECKER_ENABLED=false
WALLET_CHECKER_INTERVAL=3600
WALLET_CHECK_BATCH_SIZE=100

# Logging
LOG_LEVEL=INFO

# Upload Directory
UPLOAD_DIR=data/incoming/uploads
EOF
            print_success "Backend .env created with defaults"
        fi
    else
        print_info "Backend .env already exists"
    fi
    
    # Frontend .env
    if [ ! -f "$FRONTEND_DIR/.env" ]; then
        if [ -f "$FRONTEND_DIR/.env.example" ]; then
            print_info "Creating frontend .env from example..."
            cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
            print_success "Frontend .env created"
        else
            print_info "Creating frontend .env..."
            echo "VITE_API_URL=http://localhost:8000" > "$FRONTEND_DIR/.env"
            print_success "Frontend .env created"
        fi
    else
        print_info "Frontend .env already exists"
    fi
}

create_directories() {
    print_step "Creating necessary directories..."
    
    mkdir -p "$BACKEND_DIR/data/incoming/uploads"
    mkdir -p "$BACKEND_DIR/data/processed"
    mkdir -p "$LOG_DIR"
    
    print_success "Directories created"
}

init_database() {
    print_step "Initializing database..."
    cd "$BACKEND_DIR"
    
    source venv/bin/activate
    
    python3 -c "from app.database import Base, engine; Base.metadata.create_all(engine)" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Database initialized"
    else
        print_warning "Database initialization had issues (may already exist)"
    fi
    
    cd "$SCRIPT_DIR"
}

################################################################################
# Service Management Functions
################################################################################

start_backend() {
    print_step "Starting backend services..."
    cd "$BACKEND_DIR"
    
    source venv/bin/activate
    
    # Load environment variables (filter out comments and empty lines)
    if [ -f ".env" ]; then
        set -a
        source <(grep -v '^#' .env | grep -v '^\s*$' | sed 's/\s*#.*//')
        set +a
    fi
    
    # Start API server in background
    print_info "Starting API server on port ${API_PORT:-8000}..."
    nohup python3 -m uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --reload > "$LOG_DIR/api.log" 2>&1 &
    API_PID=$!
    echo $API_PID > "$LOG_DIR/api.pid"
    
    # Wait a moment for API to start
    sleep 3
    
    # Check if API is running
    if kill -0 $API_PID 2>/dev/null; then
        print_success "API server started (PID: $API_PID)"
    else
        print_error "API server failed to start. Check $LOG_DIR/api.log"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

start_frontend() {
    print_step "Starting frontend..."
    cd "$FRONTEND_DIR"
    
    # Start Vite dev server in background
    print_info "Starting frontend dev server..."
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
    
    sleep 3
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend started (PID: $FRONTEND_PID)"
    else
        print_error "Frontend failed to start. Check $LOG_DIR/frontend.log"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

stop_services() {
    print_step "Stopping all services..."
    
    # Stop API
    if [ -f "$LOG_DIR/api.pid" ]; then
        API_PID=$(cat "$LOG_DIR/api.pid")
        if kill -0 $API_PID 2>/dev/null; then
            kill $API_PID 2>/dev/null
            print_info "Stopped API server (PID: $API_PID)"
        fi
        rm -f "$LOG_DIR/api.pid"
    fi
    
    # Stop Frontend
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid")
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID 2>/dev/null
            print_info "Stopped frontend (PID: $FRONTEND_PID)"
        fi
        rm -f "$LOG_DIR/frontend.pid"
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    print_success "All services stopped"
}

health_check() {
    print_step "Health Check"
    
    # Check Backend
    echo -n "  Backend (Port 8000): "
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        BACKEND_OK=1
    else
        echo -e "${RED}✗ Not Running${NC}"
        BACKEND_OK=0
    fi
    
    # Check Frontend
    echo -n "  Frontend (Port 3000): "
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        FRONTEND_OK=1
    else
        echo -e "${RED}✗ Not Running${NC}"
        FRONTEND_OK=0
    fi
    
    # Show database stats if backend is running
    if [ "$BACKEND_OK" = "1" ]; then
        echo ""
        print_info "Database Statistics:"
        curl -s http://localhost:8000/api/stats 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  Unable to fetch stats"
    fi
}

show_logs() {
    SERVICE=$1
    case "$SERVICE" in
        api|backend)
            tail -f "$LOG_DIR/api.log"
            ;;
        frontend)
            tail -f "$LOG_DIR/frontend.log"
            ;;
        *)
            tail -f "$LOG_DIR/api.log" "$LOG_DIR/frontend.log"
            ;;
    esac
}

################################################################################
# Main Commands
################################################################################

cmd_install() {
    print_banner
    print_step "Installing Snatchbase..."
    
    check_python || exit 1
    check_node
    check_archive_tools
    
    create_directories
    setup_backend
    setup_frontend
    create_env_files
    init_database
    
    echo ""
    print_success "Installation complete!"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Edit configuration: $BACKEND_DIR/.env"
    echo "  2. Start the application: ./start.sh start"
    echo ""
}

cmd_start() {
    print_banner
    
    # Check if already running
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_warning "Backend is already running"
    else
        # Quick setup check
        if [ ! -d "$BACKEND_DIR/venv" ]; then
            print_info "First run detected, running installation..."
            cmd_install
        fi
        
        start_backend
    fi
    
    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
        if command -v node &> /dev/null && [ -d "$FRONTEND_DIR/node_modules" ]; then
            start_frontend
        else
            print_warning "Frontend not available (Node.js or dependencies missing)"
        fi
    else
        print_warning "Frontend is already running"
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${GREEN}✨ Snatchbase is running!${NC}"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📊 Access Points:"
    echo "  • Frontend:  http://localhost:3000"
    echo "  • API:       http://localhost:8000"
    echo "  • API Docs:  http://localhost:8000/docs"
    echo ""
    echo "🔧 Commands:"
    echo "  • Check status:  ./start.sh status"
    echo "  • View logs:     ./start.sh logs"
    echo "  • Stop:          ./start.sh stop"
    echo ""
}

cmd_stop() {
    print_banner
    stop_services
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    print_banner
    health_check
}

cmd_logs() {
    show_logs "$1"
}

cmd_help() {
    print_banner
    echo "Usage: ./start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install     - Full installation (dependencies, config, database)"
    echo "  start       - Start all services (auto-install if needed)"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  status      - Show service status and health check"
    echo "  logs [svc]  - View logs (api, frontend, or all)"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start.sh              # Same as ./start.sh start"
    echo "  ./start.sh install      # Full installation"
    echo "  ./start.sh logs api     # View API logs"
    echo ""
}

################################################################################
# Main Entry Point
################################################################################

case "${1:-start}" in
    install)
        cmd_install
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs "$2"
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        print_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
