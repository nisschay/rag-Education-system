# Backend Dockerfile - FastAPI with Python 3.12
# 
# This Dockerfile creates a container image for the RAG Education backend.
# 
# How it works:
# 1. FROM: Starts with a slim Python 3.12 image (about 150MB)
# 2. WORKDIR: Sets /app as the working directory inside the container
# 3. COPY requirements.txt: Copies dependencies file first (for Docker layer caching)
# 4. RUN pip install: Installs Python packages
# 5. COPY . .: Copies all application code
# 6. CMD: The command that runs when the container starts
#
# Build: docker build -t rag-backend ./backend
# Run:   docker run -p 8000:8000 --env-file .env rag-backend

FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p storage uploads storage/chroma_db

# Expose the port FastAPI runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
