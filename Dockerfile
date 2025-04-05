FROM python:3.9-slim

WORKDIR /app

# Install essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Make wrapper executable
RUN chmod +x wrapper.py

# Install core dependencies first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir flask==2.3.3 werkzeug==2.3.7 && \
    pip install --no-cache-dir "Pillow<11.0.0" && \
    pip install --no-cache-dir requests>=2.30.0 python-dotenv>=1.0.0 && \
    pip install --no-cache-dir google-generativeai==0.3.1 protobuf==4.24.4 && \
    pip install --no-cache-dir gunicorn>=21.2.0

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create temp_files directory needed by the app
RUN mkdir -p temp_files

# Expose the port
EXPOSE ${PORT}

# Run the application with the wrapper script
CMD ["python", "wrapper.py"] 