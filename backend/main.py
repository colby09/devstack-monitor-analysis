#!/usr/bin/env python3
"""
DevStack Health Monitor Plugin
Main application entry point - FIXED VERSION
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import api_router
from app.services.monitor import HealthMonitor
from app.services.websocket import WebSocketManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# WebSocket manager
websocket_manager = WebSocketManager()

# Health monitor
health_monitor = HealthMonitor(websocket_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting DevStack Health Monitor...")
    await health_monitor.start_monitoring()
    logger.info(f"Health Monitor started on port {settings.PORT}")
    logger.info(f"Dashboard available at: http://localhost:{settings.PORT}")
    logger.info(f"API documentation at: http://localhost:{settings.PORT}/api/docs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DevStack Health Monitor...")
    await health_monitor.stop_monitoring()

# Create FastAPI app
app = FastAPI(
    title="DevStack Health Monitor",
    description="Real-time monitoring for OpenStack DevStack instances and services",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/api/debug")
async def debug_routes():
    """Debug endpoint to check routes"""
    return {"message": "API routing works", "available_routes": ["/api/services", "/api/instances", "/api/metrics", "/api/alerts"]}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DevStack Health Monitor",
        "version": "1.0.0"
    }

# Serve static files (frontend build)
dist_path = Path("../dist")
assets_path = Path("../dist/assets")

if dist_path.exists() and assets_path.exists():
    # Mount static assets with correct path
    app.mount("/assets", StaticFiles(directory="../dist/assets"), name="assets")
    
    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon"""
        favicon_path = dist_path / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        return HTMLResponse("", status_code=404)
    
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """Serve frontend application"""
        # Skip API routes and WebSocket
        if full_path.startswith("api/") or full_path.startswith("ws") or full_path == "health":
            return HTMLResponse("Not Found", status_code=404)
        
        # Serve static files directly from assets
        if full_path.startswith("assets/"):
            file_path = dist_path / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return HTMLResponse("File not found", status_code=404)
        
        # For all other routes, serve index.html (SPA routing)
        index_path = dist_path / "index.html"
        if index_path.exists():
            logger.info(f"Serving index.html for path: {full_path}")
            return FileResponse(index_path, media_type="text/html")
        else:
            logger.error(f"index.html not found at {index_path}")
            return HTMLResponse(
                "<h1>Frontend not found</h1><p>Please build the frontend first: npm run build</p>", 
                status_code=404
            )
    
    logger.info(f"Frontend static files mounted from: {dist_path}")
    logger.info(f"Assets directory: {assets_path}")
else:
    logger.warning(f"Frontend dist directory not found at {dist_path}. Only API will be available.")
    
    @app.get("/")
    async def root():
        """Root endpoint when frontend is not available"""
        return HTMLResponse("""
        <html>
            <head><title>DevStack Health Monitor</title></head>
            <body>
                <h1>DevStack Health Monitor</h1>
                <p>Frontend not built. Please run: <code>npm run build</code></p>
                <p><a href="/api/docs">API Documentation</a></p>
            </body>
        </html>
        """)

if __name__ == "__main__":
    # Production mode - no auto-reload
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )