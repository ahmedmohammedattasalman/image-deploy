FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Pillow and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files first (excluding requirements.txt)
COPY main.py .
COPY templates/ ./templates/
COPY setup_supabase.py .
COPY .env.example .

# Install dependencies directly (skip requirements.txt)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir flask==2.3.3 && \
    pip install --no-cache-dir google-generativeai==0.5.0 && \
    pip install --no-cache-dir "Pillow<11.0.0" && \
    pip install --no-cache-dir python-supabase==0.7.0 && \
    pip install --no-cache-dir python-dotenv>=1.0.0 && \
    pip install --no-cache-dir werkzeug==2.3.7 && \
    pip install --no-cache-dir itsdangerous==2.1.2 && \
    pip install --no-cache-dir jinja2==3.1.2 && \
    pip install --no-cache-dir requests>=2.30.0 && \
    pip install --no-cache-dir gunicorn>=21.2.0

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0

# Create temp_files directory that might be needed by the app
RUN mkdir -p temp_files

# Expose the port
EXPOSE ${PORT}

# Run the application
CMD ["python", "main.py"] 