"""
Snatchbase - Stealer Log Aggregator API
A modern stealer log search engine and aggregator

Simplified main application file - routes are modularized
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from app.database import engine
from app.models import Base

# Import routers
from app.routers import wallets, credentials, devices, statistics, files, credit_cards

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Snatchbase API",
    description="Stealer Log Aggregator and Search Engine",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(credentials.router, prefix="/api", tags=["credentials"])
app.include_router(devices.router, prefix="/api", tags=["devices"])
app.include_router(statistics.router, prefix="/api", tags=["statistics"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(wallets.router, prefix="/api", tags=["wallets"])
app.include_router(credit_cards.router, prefix="/api", tags=["credit-cards"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Snatchbase API - Stealer Log Aggregator"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "snatchbase-api"}


# File watcher is now handled by separate service
# See: launcher/file_watcher_service.py


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
