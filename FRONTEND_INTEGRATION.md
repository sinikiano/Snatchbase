# Frontend-Backend Integration Guide

## Overview

The Snatchbase frontend is a modern React + TypeScript application that connects to the FastAPI backend through a simple proxy configuration.

## Architecture

```
Frontend (React + Vite)  →  Backend (FastAPI)
Port 3000                    Port 8000
/api/* requests          →  /api/* endpoints
```

## Quick Start

### Start Everything at Once

```bash
./start_full_stack.sh
```

This will start:
- All backend services (API, Telegram Bot, File Watcher, Wallet Checker)
- Frontend development server

### Start Components Separately

**Backend Only:**
```bash
./start_snatchbase_v2.sh
```

**Frontend Only:**
```bash
./start_frontend.sh
```

## API Integration

### Endpoint Structure

All API endpoints are prefixed with `/api`:

```
Frontend Request          Backend Route
GET /api/stats        →  /api/stats
GET /api/devices      →  /api/devices
POST /api/search      →  /api/search/credentials
```

### API Client Configuration

The frontend uses axios with automatic proxy:

**Location:** `frontend/src/services/api.ts`

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

**Vite Proxy:** `frontend/vite.config.ts`

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## Available Endpoints

### Statistics
- `GET /api/stats` - General statistics
- `GET /api/stats/domains` - Top domains
- `GET /api/stats/countries` - Country distribution
- `GET /api/stats/stealers` - Stealer types
- `GET /api/stats/browsers` - Browser distribution
- `GET /api/stats/tlds` - Top-level domains

### Search
- `GET /api/search/credentials` - Search credentials
- `GET /api/search/systems` - Search systems
- `GET /api/search/export` - Export results

### Devices
- `GET /api/devices` - List devices
- `GET /api/devices/{id}` - Device details
- `GET /api/devices/{id}/credentials` - Device credentials
- `GET /api/devices/{id}/files` - Device files
- `GET /api/devices/{id}/software` - Device software

### Wallets
- `GET /api/wallets` - List wallets
- `GET /api/wallets/{id}` - Wallet details
- `GET /api/stats/wallets` - Wallet statistics
- `POST /api/wallets/check-balance` - Check balances

### Files
- `GET /api/files/{id}` - File details

## Environment Variables

Create `frontend/.env` for custom configuration:

```env
# API URL (defaults to http://localhost:8000)
VITE_API_URL=http://localhost:8000

# Other custom variables
VITE_APP_NAME=Snatchbase
```

## Development

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
cd frontend
npm run dev
```

### Build for Production

```bash
cd frontend
npm run build
```

### Preview Production Build

```bash
cd frontend
npm run preview
```

## CORS Configuration

The backend is configured to accept requests from any origin:

**Location:** `backend/app/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Issue: Frontend can't connect to backend

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify proxy configuration in `vite.config.ts`
3. Check browser console for CORS errors

### Issue: API endpoints return 404

**Solution:**
1. Ensure all endpoints use `/api` prefix
2. Verify backend routers are registered in `main.py`
3. Check API documentation: `http://localhost:8000/docs`

### Issue: Module not found errors

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## API Response Types

All API responses follow consistent structure:

**Search Results:**
```typescript
{
  results: T[],
  total: number,
  limit: number,
  offset: number
}
```

**Statistics:**
```typescript
{
  total_credentials: number,
  total_systems: number,
  unique_domains: number,
  // ... more stats
}
```

## Testing API Integration

### Test Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "snatchbase-api"}
```

### Test Frontend Connection

1. Start both frontend and backend
2. Open browser: `http://localhost:3000`
3. Check browser console for any errors
4. Verify API calls in Network tab

## Access Points

- **Frontend:** http://localhost:3000
- **API Server:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc

## Stack Details

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite 4
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State:** React Query
- **Routing:** React Router v6

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.10+
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Architecture:** Service-oriented (modular)

## Configuration Files

**No changes needed** - all frontend configuration is preserved:

- ✅ `frontend/package.json` - Dependencies unchanged
- ✅ `frontend/vite.config.ts` - Updated proxy only
- ✅ `frontend/tailwind.config.js` - Unchanged
- ✅ `frontend/tsconfig.json` - Unchanged
- ✅ `frontend/postcss.config.js` - Unchanged
- ✅ `frontend/src/services/api.ts` - Updated API paths only

## Next Steps

1. **Start the application:** `./start_full_stack.sh`
2. **Access frontend:** http://localhost:3000
3. **View API docs:** http://localhost:8000/docs
4. **Monitor services:** `python -m backend.launcher.snatchctl status`

Everything is synced and ready to go! 🚀
