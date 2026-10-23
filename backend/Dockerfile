# Use official lightweight Python 3.11 runtime
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only first to prevent downloading 3.5GB of CUDA packages and avoid disk-space errors
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the local embedding model during build for instant offline startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy backend application source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Automatically run seed script (creates tables, demo users, indexes KB), then launch Uvicorn
CMD ["sh", "-c", "python scripts/seed_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
