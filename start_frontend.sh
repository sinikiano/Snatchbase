#!/bin/bash
# Frontend startup script for Snatchbase

set -e

echo "🚀 Starting Snatchbase Frontend..."

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Must run from Snatchbase root directory"
    exit 1
fi

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "✅ Starting development server on http://localhost:3000"
npm run dev
