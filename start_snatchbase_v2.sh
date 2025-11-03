#!/bin/bash

echo "🚀 Starting Snatchbase Intelligence Platform v2.0"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "backend/launcher/service_manager.py" ]; then
    print_error "Please run this script from the Snatchbase root directory"
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p backend/data/incoming/uploads
mkdir -p backend/data/processed
mkdir -p backend/logs
print_success "Directories created"

# Check and setup Python virtual environment
print_status "Checking Python environment..."
cd backend

if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

source venv/bin/activate

# Install/Update Python dependencies
print_status "Installing/updating Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

# Setup database
print_status "Setting up database..."
if [ -f "setup_db.sh" ]; then
    bash setup_db.sh > /dev/null 2>&1
    print_success "Database setup complete"
else
    print_warning "Database setup script not found (setup_db.sh)"
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    print_status "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
    print_success "Environment variables loaded"
else
    print_warning "No .env file found. Using defaults from .env.template"
    print_warning "Create .env from .env.template to customize settings"
fi

# Start backend services using service manager
print_status "Starting backend services..."
python3 launcher/service_manager.py > /tmp/snatchbase-services.log 2>&1 &
SERVICES_PID=$!

# Wait for backend API to be ready
print_status "Waiting for API to start..."
for i in {1..15}; do
    if curl -s http://localhost:${API_PORT:-8000}/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

if curl -s http://localhost:${API_PORT:-8000}/health > /dev/null 2>&1; then
    print_success "Backend services started (PID: $SERVICES_PID)"
else
    print_error "Backend API failed to start. Check logs: tail -f /tmp/snatchbase-services.log"
    kill $SERVICES_PID 2>/dev/null
    exit 1
fi

cd ..

# Check and setup Node.js dependencies
print_status "Checking frontend dependencies..."
cd frontend

if [ ! -d "node_modules" ]; then
    print_warning "Node modules not found. Installing..."
    npm install --silent
    if [ $? -eq 0 ]; then
        print_success "Frontend dependencies installed"
    else
        print_error "Failed to install frontend dependencies"
        kill $SERVICES_PID 2>/dev/null
        exit 1
    fi
else
    print_success "Frontend dependencies found"
fi

# Start frontend
print_status "Starting frontend server..."
npm run dev > /tmp/snatchbase-frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
print_status "Waiting for frontend to start..."
sleep 3
print_success "Frontend server started (PID: $FRONTEND_PID)"

cd ..

# Show info
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🎉 Snatchbase v2.0 is running! 🎉                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Access Points:"
echo "   • Frontend:    http://localhost:3000"
echo "   • Backend API: http://localhost:${API_PORT:-8000}"
echo "   • API Docs:    http://localhost:${API_PORT:-8000}/docs"
echo ""
echo "🔧 Active Services:"
echo "   • API Server: ✅"
echo "   • File Watcher: $([ "${FILE_WATCHER_ENABLED:-true}" = "true" ] && echo "✅" || echo "⏭️")"
echo "   • Telegram Bot: $([ "${TELEGRAM_ENABLED:-true}" = "true" ] && [ ! -z "${TELEGRAM_BOT_TOKEN}" ] && echo "✅" || echo "⏭️")"
echo "   • Wallet Checker: $([ "${WALLET_CHECKER_ENABLED:-false}" = "true" ] && echo "✅" || echo "⏭️")"
echo ""
echo "📦 Features:"
echo "   • Credential Search & Export"
echo "   • Wallet Balance Checking (ETH/SOL/BTC)"
echo "   • Device & System Analytics"
echo "   • Auto ZIP Ingestion"
if [ "${TELEGRAM_ENABLED:-true}" = "true" ] && [ ! -z "${TELEGRAM_BOT_TOKEN}" ]; then
    echo "   • Telegram File Upload"
fi
echo ""
echo "📝 Logs:"
echo "   • All Services: tail -f /tmp/snatchbase-services.log"
echo "   • Frontend:     tail -f /tmp/snatchbase-frontend.log"
echo "   • Individual:   tail -f backend/logs/*.log"
echo ""
echo "💡 New Architecture Benefits:"
echo "   • Independent service processes (no cascade failures)"
echo "   • Automatic health monitoring and restarts"
echo "   • Modular route organization"
echo "   • Easy to enable/disable features via .env"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Cleanup function
cleanup() {
    echo ""
    print_status "Stopping all services..."
    kill $SERVICES_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    sleep 2
    pkill -f "launcher/service_manager.py" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    print_success "All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running
wait

