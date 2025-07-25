# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file first (for better Docker layer caching)
COPY server/requirements.txt ./requirements.txt
COPY server/requirements/ ./requirements/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire server directory
COPY server/ ./

# Create sessions directory
RUN mkdir -p sessions logs

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Railway will set the PORT environment variable)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start command - use uvicorn directly
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 1"]