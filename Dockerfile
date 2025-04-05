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

# Copy application code WITH requirements.txt
COPY wrapper.py ./
COPY main.py ./
COPY templates ./templates/
COPY setup_supabase.py ./
COPY .env.example ./
COPY requirements.txt ./

# Make wrapper executable
RUN chmod +x wrapper.py

# Install dependencies (requirements.txt already contains the correct versions)
RUN pip install --no-cache-dir -r requirements.txt

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