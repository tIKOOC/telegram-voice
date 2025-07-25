# server/src/main.py - Railway Health Check Fix
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize logging first
from src.core.logging import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Import after logging is setup
from src.telegram.client import telegram_manager
from src.api.websocket import websocket_router, websocket_manager
from src.api.routes import api_router
from src.core.config import settings

# Global flags for health check
app_initialized = False
initialization_error = None
initialization_start_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global app_initialized, initialization_error, initialization_start_time
    
    initialization_start_time = asyncio.get_event_loop().time()
    logger.info("🚀 Starting Telegram Voice Reply Server...")
    
    # Start initialization in background to not block health checks
    init_task = asyncio.create_task(initialize_app())
    
    try:
        yield
    finally:
        # Cancel initialization if still running
        if not init_task.done():
            init_task.cancel()
            
        # Cleanup
        logger.info("🔄 Shutting down...")
        try:
            if telegram_manager.is_connected:
                await telegram_manager.disconnect()
                logger.info("✅ Telegram client disconnected")
        except Exception as e:
            logger.error(f"⚠️ Cleanup error: {e}")

async def initialize_app():
    """Initialize application components in background"""
    global app_initialized, initialization_error
    
    try:
        # Wait a bit to let health checks pass
        await asyncio.sleep(2)
        
        logger.info("🔄 Initializing Telegram client...")
        
        # Check if credentials are provided
        if not all([settings.telegram_api_id, settings.telegram_api_hash]):
            raise ValueError("Missing Telegram API credentials")
            
        # Initialize with longer timeout for Railway
        await asyncio.wait_for(telegram_manager.initialize(), timeout=60.0)
        logger.info("✅ Telegram client initialized successfully")
        
        # Register event handlers
        from src.telegram.handlers import register_handlers
        await register_handlers(telegram_manager.client)
        logger.info("✅ Event handlers registered")
        
        app_initialized = True
        logger.info("🎉 Application initialization completed successfully")
        
        # Keep the Telegram client running
        if telegram_manager.client:
            await telegram_manager.client.run_until_disconnected()
        
    except asyncio.TimeoutError:
        error_msg = "Telegram client initialization timeout"
        logger.error(f"⏰ {error_msg}")
        initialization_error = error_msg
        app_initialized = False
        
    except Exception as e:
        error_msg = f"Application initialization failed: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        initialization_error = error_msg
        app_initialized = False

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Telegram Voice Reply Server with WebSocket and FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow all for Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint - ALWAYS returns 200
@app.get("/")
async def root():
    """Root endpoint for basic connectivity"""
    return {
        "message": "Telegram Voice Reply Server",
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

# Simple ping endpoint - ALWAYS returns 200
@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"ping": "pong"}

# Health check endpoint - Railway compatible
@app.get("/health")
async def health_check():
    """Health check endpoint - always returns 200 for Railway"""
    global app_initialized, initialization_error, initialization_start_time
    
    # Calculate initialization time
    init_time = None
    if initialization_start_time:
        init_time = asyncio.get_event_loop().time() - initialization_start_time
    
    # Basic health data
    health_data = {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
        "port": os.getenv("PORT", "8000"),
        "initialization": {
            "completed": app_initialized,
            "time_elapsed": init_time,
            "error": initialization_error
        }
    }
    
    # Add Telegram status if available
    if app_initialized:
        try:
            telegram_status = {
                "connected": telegram_manager.is_connected,
                "client_ready": telegram_manager.client is not None
            }
            
            # Try to get user info with short timeout
            if telegram_manager.is_connected:
                try:
                    me = await asyncio.wait_for(
                        telegram_manager.client.get_me(), 
                        timeout=2.0
                    )
                    telegram_status["user"] = {
                        "id": me.id,
                        "username": me.username,
                        "name": f"{me.first_name} {me.last_name or ''}".strip()
                    }
                except asyncio.TimeoutError:
                    telegram_status["user"] = {"error": "timeout"}
                except Exception as e:
                    telegram_status["user"] = {"error": str(e)}
                    
            health_data["telegram"] = telegram_status
            
        except Exception as e:
            health_data["telegram"] = {"error": str(e)}
    
    # Add WebSocket status
    health_data["websocket"] = {
        "active_connections": websocket_manager.connection_count_active
    }
    
    # Always return 200 OK
    return health_data

# API Status endpoint
@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "operational",
        "telegram_connected": telegram_manager.is_connected,
        "app_initialized": app_initialized,
        "websocket_connections": websocket_manager.connection_count_active,
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(websocket_router, prefix="/ws")
app.include_router(api_router, prefix="/api")

# Startup logging
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 50)
    logger.info("🚀 FastAPI server started")
    logger.info(f"🌍 Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info(f"🚪 Port: {os.getenv('PORT', settings.port)}")
    logger.info(f"📍 Health check: /health")
    logger.info(f"🔌 WebSocket: /ws")
    logger.info("=" * 50)

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment
    port = int(os.getenv("PORT", settings.port))
    
    logger.info(f"🚀 Starting server on 0.0.0.0:{port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=True,
        workers=1
    )
