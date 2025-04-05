FROM python:3.9-slim

WORKDIR /app

# Install essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x wrapper.py
RUN chmod +x railway_entry.py

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir flask==2.3.3 werkzeug==2.3.7 itsdangerous==2.1.2 jinja2==3.1.2 && \
    pip install --no-cache-dir "Pillow<11.0.0" requests>=2.30.0 python-dotenv>=1.0.0 && \
    pip install --no-cache-dir google-generativeai==0.3.1 protobuf==4.24.4 && \
    pip install --no-cache-dir gunicorn>=21.2.0

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create temp_files directory
RUN mkdir -p temp_files

# Expose the port
EXPOSE ${PORT}

# Add a healthcheck
HEALTHCHECK --interval=5s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/healthcheck || exit 1

# Start with gunicorn using our railway entry point
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 2 --timeout 60 railway_entry:app 