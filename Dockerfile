FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy ALL application files first
COPY . .

# Display the requirements file content for debugging
RUN cat requirements.txt

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# Make wrapper executable
RUN chmod +x wrapper.py

# Install dependencies one by one with verbose output
RUN pip install --no-cache-dir -v flask==2.3.3 && \
    pip install --no-cache-dir -v werkzeug==2.3.7 && \
    pip install --no-cache-dir -v itsdangerous==2.1.2 && \
    pip install --no-cache-dir -v jinja2==3.1.2 && \
    pip install --no-cache-dir -v "Pillow<11.0.0" && \
    pip install --no-cache-dir -v "python-dotenv>=1.0.0" && \
    pip install --no-cache-dir -v "requests>=2.30.0" && \
    pip install --no-cache-dir -v "gunicorn>=21.2.0" && \
    pip install --no-cache-dir -v google-generativeai==0.3.1 && \
    pip install --no-cache-dir -v protobuf==4.24.4 && \
    pip install --no-cache-dir -v "supabase-py>=1.0.3" && \
    pip list

# Create compatibility check script
RUN echo 'import sys; sys.path.insert(0, "/app"); import wrapper; print("Wrapper module initialized")' > /app/compatibility_check.py

# Check if wrapper works correctly
RUN python /app/compatibility_check.py || echo "Warning: Compatibility layer might not be working"

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create temp_files directory needed by the app
RUN mkdir -p temp_files

# Expose the port
EXPOSE ${PORT}

# Run the application with the wrapper script
CMD ["python", "wrapper.py"] 