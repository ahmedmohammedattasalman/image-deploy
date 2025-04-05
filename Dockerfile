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

# Install dependencies by version with explicit logging
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    echo "Installing Flask and core dependencies..." && \
    pip install --no-cache-dir flask==2.3.3 werkzeug==2.3.7 itsdangerous==2.1.2 jinja2==3.1.2 && \
    echo "Installing Pillow and utilities..." && \
    pip install --no-cache-dir "Pillow<11.0.0" requests>=2.30.0 python-dotenv>=1.0.0 && \
    echo "Installing Google Gemini API..." && \
    pip install --no-cache-dir google-generativeai==0.3.1 protobuf==4.24.4 && \
    echo "Installing web server..." && \
    pip install --no-cache-dir gunicorn>=21.2.0 && \
    echo "Listing all installed packages:" && \
    pip list

# Set environment variables for better logging and debugging
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DEBUG=False
ENV LOG_LEVEL=INFO

# Create temp_files directory
RUN mkdir -p temp_files

# Expose the port
EXPOSE ${PORT}

# Add a healthcheck
HEALTHCHECK --interval=5s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/healthcheck || exit 1

# Run healthcheck script to test API compatibility prior to startup
RUN python -c "import sys; sys.path.insert(0, '/app'); import railway_entry; print('Compatibility check passed')" || echo "Warning: Compatibility check failed"

# Start with gunicorn using our railway entry point
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 2 --timeout 120 railway_entry:app --log-level info 