#!/bin/bash

echo "🚀 Starting Snatchbase Intelligence Platform"
echo "============================================"
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

# Function to stop all services
stop_all() {
    print_status "Stopping all services..."
    pkill -f "uvicorn app.main:app" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    pkill -f "run_telegram_bot.py" 2>/dev/null
    sleep 2
    print_success "All services stopped"
}

# Trap to cleanup on exit
trap stop_all EXIT INT TERM

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    print_error "Please run this script from the Snatchbase root directory"
    exit 1
fi

# Stop any running services first
stop_all

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p backend/data/incoming/uploads
mkdir -p backend/data/processed
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
        exit 1
    fi
else
    print_success "Frontend dependencies found"
fi

cd ..

# Load environment variables if .env exists
if [ -f "backend/.env" ]; then
    print_status "Loading environment variables..."
    export $(cat backend/.env | grep -v '^#' | xargs)
    print_success "Environment variables loaded"
fi

# Start backend
print_status "Starting backend server..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/snatchbase-backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
print_status "Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/ > /dev/null 2>&1; then
        break
    fi
    sleep 1
done
print_success "Backend server started (PID: $BACKEND_PID)"

# Start Telegram bot if configured
if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_ALLOWED_USER_ID" ]; then
    print_status "Starting Telegram bot..."
    cd backend
    source venv/bin/activate
    python3 run_telegram_bot.py > /tmp/snatchbase-telegram-bot.log 2>&1 &
    TELEGRAM_BOT_PID=$!
    cd ..
    print_success "Telegram bot started (PID: $TELEGRAM_BOT_PID)"
else
    print_warning "Telegram bot not configured (skipping)"
    TELEGRAM_BOT_PID=""
fi

# Start frontend
print_status "Starting frontend server..."
cd frontend
npm run dev > /tmp/snatchbase-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready
print_status "Waiting for frontend to start..."
sleep 3
print_success "Frontend server started (PID: $FRONTEND_PID)"

# Show info
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║             🎉 Snatchbase is running! 🎉                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Access Points:"
echo "   • Frontend:    http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs:    http://localhost:8000/docs"
if [ ! -z "$TELEGRAM_BOT_PID" ]; then
    echo "   • Telegram Bot: Active (Send files to @ermachook_bot)"
fi
echo ""
echo "🔧 Features Available:"
echo "   • Credential Search & Export (TXT/CSV)"
echo "   • Wallet Balance Checking (ETH/SOL/BTC)"
echo "   • Device & System Analytics"
echo "   • Auto ZIP Ingestion"
if [ ! -z "$TELEGRAM_BOT_PID" ]; then
    echo "   • Telegram File Upload"
fi
echo ""
echo "📦 Auto-Ingestion:"
echo "   • Drop ZIP files into: backend/data/incoming/uploads/"
if [ ! -z "$TELEGRAM_BOT_PID" ]; then
    echo "   • Send ZIP files via Telegram: @ermachook_bot"
fi
echo "   • Backend automatically processes them"
echo "   • View results in the web interface"
echo ""
echo "📝 Logs:"
echo "   • Backend:  tail -f /tmp/snatchbase-backend.log"
echo "   • Frontend: tail -f /tmp/snatchbase-frontend.log"
if [ ! -z "$TELEGRAM_BOT_PID" ]; then
    echo "   • Telegram: tail -f /tmp/snatchbase-telegram-bot.log"
fi
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    if [ ! -z "$TELEGRAM_BOT_PID" ]; then
        kill $TELEGRAM_BOT_PID 2>/dev/null
    fi
    echo "✓ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running
wait
