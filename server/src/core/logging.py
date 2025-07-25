# server/src/core/logging.py
import sys
import logging
import logging.config
from datetime import datetime
from pathlib import Path

def setup_logging():
    """Cấu hình logging cho ứng dụng"""
    
    # Tạo thư mục logs nếu chưa có
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Log file với timestamp
    log_file = log_dir / f"telegram_voice_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)-25s | %(funcName)-20s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)-8s | %(name)-20s | %(message)s"
            },
            "json": {
                "()": JsonFormatter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(log_dir / "errors.log"),
                "maxBytes": 5242880,  # 5MB
                "backupCount": 3,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file", "error_file"],
                "level": "DEBUG",
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "fastapi": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "telethon": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "websockets": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("🚀 Logging system initialized")
    logger.info(f"📁 Log files: {log_dir.absolute()}")

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter cho structured logging"""
    
    def format(self, record):
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Thêm exception info nếu có
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Thêm extra fields nếu có
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)