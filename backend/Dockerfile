# Dockerfile for Aurora Backend - HuggingFace Spaces deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into the container
COPY . .

# Ensure the CA certificate is available at /app/ca.pem
# (The ca.pem file should already be in the backend directory)
RUN if [ ! -f ca.pem ]; then echo "WARNING: ca.pem not found! Please ensure it's in the backend directory."; fi

# Build ChromaDB vector store from data directory
RUN echo "Building ChromaDB vector store..." && \
    python -c "from rag import build_vectorstore; build_vectorstore('./data')" && \
    echo "ChromaDB vector store built successfully!"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port 7860 as required by HuggingFace Spaces
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/health')"

# Start the FastAPI application with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
