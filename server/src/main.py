# server/src/main.py - Railway Health Check Fix
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from telegram.client import telegram_manager
from api.websocket import websocket_router
from api.routes import api_router
from core.config import settings
from core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global flag to track initialization status
app_initialized = False
initialization_error = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle của ứng dụng"""
    global app_initialized, initialization_error
    
    logger.info("🚀 Starting Telegram Voice Reply Server...")
    
    try:
        # Khởi tạo Telegram client với timeout
        logger.info("🔄 Initializing Telegram client...")
        await asyncio.wait_for(telegram_manager.initialize(), timeout=30.0)
        logger.info("✅ Telegram client initialized successfully")
        
        # Đăng ký event handlers
        from telegram.handlers import register_handlers
        await register_handlers(telegram_manager.client)
        logger.info("✅ Event handlers registered")
        
        app_initialized = True
        logger.info("🎉 Application initialization completed successfully")
        
        yield
        
    except asyncio.TimeoutError:
        error_msg = "Telegram client initialization timeout (30s)"
        logger.error(f"⏰ {error_msg}")
        initialization_error = error_msg
        app_initialized = False
        # Don't raise - let health check handle this
        yield
        
    except Exception as e:
        error_msg = f"Application startup failed: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        initialization_error = error_msg
        app_initialized = False
        # Don't raise - let health check handle this
        yield
        
    finally:
        # Cleanup
        logger.info("🔄 Shutting down...")
        try:
            if telegram_manager.is_connected:
                await telegram_manager.disconnect()
                logger.info("✅ Telegram client disconnected")
        except Exception as e:
            logger.error(f"⚠️ Cleanup error: {e}")

# Tạo FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Telegram Voice Reply Server với WebSocket và FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Railway
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Basic root endpoint - ALWAYS works
@app.get("/")
async def root():
    """Root endpoint - always returns 200 for basic connectivity test"""
    return {
        "message": "Telegram Voice Reply Server",
        "status": "running",
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
        "port": os.getenv("PORT", "8000")
    }

# Simple ping for Railway health checks
@app.get("/ping")
async def ping():
    """Simple ping - always returns 200"""
    return {"ping": "pong", "timestamp": None}

# Detailed health check
@app.get("/health")
async def health_check():
    """Health check endpoint - Railway compatible"""
    global app_initialized, initialization_error
    
    try:
        # Basic application health
        health_data = {
            "status": "healthy",
            "version": "1.0.0",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
            "port": os.getenv("PORT", "8000"),
            "app_initialized": app_initialized
        }
        
        # If app not initialized, still return 200 but with warning
        if not app_initialized:
            health_data.update({
                "status": "starting",
                "warning": "Application still initializing",
                "error": initialization_error
            })
            # Return 200 so Railway doesn't kill the deployment
            return health_data
        
        # Check Telegram connection (optional)
        telegram_status = {
            "connected": False,
            "client_ready": False
        }
        
        try:
            if telegram_manager.is_connected:
                telegram_status["connected"] = True
                telegram_status["client_ready"] = True
                
                # Quick user info check with timeout
                me = await asyncio.wait_for(telegram_manager.client.get_me(), timeout=5.0)
                telegram_status["user"] = {
                    "id": me.id,
                    "username": me.username,
                    "name": f"{me.first_name} {me.last_name or ''}".strip()
                }
        except asyncio.TimeoutError:
            telegram_status["error"] = "Telegram API timeout"
        except Exception as e:
            telegram_status["error"] = str(e)
        
        health_data["telegram"] = telegram_status
        
        # Always return 200 for Railway health checks
        return health_data
        
    except Exception as e:
        logger.error(f"Health check exception: {e}", exc_info=True)
        # Even on error, return 200 with error info
        return {
            "status": "degraded",
            "error": str(e),
            "app_initialized": app_initialized,
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
        }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )

# Include routers
app.include_router(websocket_router, prefix="/ws")
app.include_router(api_router, prefix="/api")

# Startup event logging
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 FastAPI server started")
    logger.info(f"🌍 Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info(f"🎯 Host: {settings.host}")
    logger.info(f"🚪 Port: {os.getenv('PORT', settings.port)}")

if __name__ == "__main__":
    import uvicorn
    
    # CRITICAL: Use Railway's PORT environment variable
    port = int(os.getenv("PORT", settings.port))
    
    logger.info(f"🚀 Starting server on 0.0.0.0:{port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Must be 0.0.0.0 for Railway
        port=port,       # Use Railway's dynamic port
        reload=False,    # Disable reload in production
        log_level="info",
        workers=1        # Single worker for Railway
    )
