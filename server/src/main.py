# server/src/main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from telegram.client import telegram_manager
from api.websocket import websocket_router
from api.routes import api_router
from core.config import settings
from core.logging import setup_logging
from fastapi import FastAPI
# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle của ứng dụng"""
    logger.info("🚀 Starting Telegram Voice Reply Server...")
    
    try:
        # Khởi tạo Telegram client
        await telegram_manager.initialize()
        logger.info("✅ Telegram client initialized")
        
        # Đăng ký event handlers
        from telegram.handlers import register_handlers
        await register_handlers(telegram_manager.client)
        logger.info("✅ Event handlers registered")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🔄 Shutting down...")
        await telegram_manager.disconnect()
        logger.info("✅ Cleanup completed")

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
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )

# Health check
@app.get("/")
async def root():
    return {
        "message": "Telegram Voice Reply Server",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint cho deployment platforms"""
    try:
        telegram_status = {
            "connected": telegram_manager.is_connected,
            "client_ready": telegram_manager.client is not None
        }
        
        if telegram_manager.is_connected:
            # Test connection
            me = await telegram_manager.client.get_me()
            telegram_status["user"] = {
                "id": me.id,
                "username": me.username,
                "name": f"{me.first_name} {me.last_name or ''}".strip()
            }
        
        return {
            "status": "healthy",
            "telegram": telegram_status,
            "debug_mode": settings.debug
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "telegram": {"connected": False}
            }
        )

# Include routers
app.include_router(websocket_router, prefix="/ws")
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )