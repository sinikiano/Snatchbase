#!/bin/bash
# Complete Snatchbase Startup Script
# Starts both backend services and frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════"
echo "   🚀 Starting Snatchbase - Complete Application"
echo "═══════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if process is running
is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# 1. Start Backend Services
echo -e "${BLUE}[1/2] Starting Backend Services...${NC}"
if [ -f "./start_snatchbase_v2.sh" ]; then
    ./start_snatchbase_v2.sh
    echo -e "${GREEN}✅ Backend services started${NC}"
else
    echo -e "${YELLOW}⚠️  Backend startup script not found, skipping...${NC}"
fi

echo ""

# 2. Start Frontend
echo -e "${BLUE}[2/2] Starting Frontend...${NC}"
if [ -f "./start_frontend.sh" ]; then
    ./start_frontend.sh &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend starting in background (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend startup script not found, skipping...${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "${GREEN}✨ Snatchbase is starting up!${NC}"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📊 Access Points:"
echo "  • Frontend:  http://localhost:3000"
echo "  • API:       http://localhost:8000"
echo "  • API Docs:  http://localhost:8000/docs"
echo ""
echo "🔧 Control Commands:"
echo "  • Check status:  python -m backend.launcher.snatchctl status"
echo "  • Stop backend:  python -m backend.launcher.snatchctl stop all"
echo "  • Stop frontend: kill $FRONTEND_PID"
echo ""
echo "📝 Logs: Check terminal output above"
echo ""
