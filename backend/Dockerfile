# Dockerfile for Aurora Backend - HuggingFace Spaces deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into the container
COPY . .

# Clean up any SQLite .db files and vector store files that might have been committed
RUN find . -name "*.db" -type f -delete && \
    find . -name "*.parquet" -type f -delete && \
    echo "Cleaned up any .db files and vector store files"

# Ensure the CA certificate is available at /app/ca.pem
# (The ca.pem file should already be in the backend directory)
RUN if [ ! -f ca.pem ]; then echo "WARNING: ca.pem not found! Please ensure it's in the backend directory."; fi

# Create writable directories for temporary data
RUN mkdir -p /tmp/data && \
    chmod -R 777 /tmp/data && \
    echo "Created temporary data directories with full permissions"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Set ownership of app directory and data directories
RUN chown -R app:app /app && \
    chown -R app:app /tmp/data

# Build vector store from data directory
RUN echo "Building vector store..." && \
    python -c "from rag import build_vectorstore; result = build_vectorstore('./data'); print('Vector store build result:', result is not None)" && \
    echo "Vector store build completed!"

# Switch to non-root user
USER app

# Expose port 7860 as required by HuggingFace Spaces
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/healthz')"

# Start the FastAPI application with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
