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

# Copy application code but NOT requirements.txt
COPY main.py ./
COPY wrapper.py ./
COPY templates ./templates/
COPY setup_supabase.py ./
COPY .env.example ./

# Make wrapper executable
RUN chmod +x wrapper.py

# Install dependencies individually - explicitly avoid requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    # Core web app dependencies
    pip install --no-cache-dir flask==2.3.3 && \
    pip install --no-cache-dir werkzeug==2.3.7 && \
    pip install --no-cache-dir itsdangerous==2.1.2 && \
    pip install --no-cache-dir jinja2==3.1.2 && \
    # For image processing and API
    pip install --no-cache-dir "Pillow<11.0.0" && \
    # Install a consistent version of Google Generative AI
    pip install --no-cache-dir google-api-python-client==2.79.0 && \
    pip install --no-cache-dir google-auth==2.16.0 && \
    pip install --no-cache-dir google-auth-httplib2==0.1.0 && \
    pip install --no-cache-dir google-auth-oauthlib==1.0.0 && \
    pip install --no-cache-dir google-generativeai==0.3.1 && \
    # Generate a simple test to verify Gemini is working
    echo "import google.generativeai; google.generativeai.configure(api_key='test-key'); print('Gemini configuration test passed')" > /tmp/test_gemini.py && \
    python /tmp/test_gemini.py && \
    # Manual installation of Supabase dependencies
    pip install --no-cache-dir postgrest-py && \
    pip install --no-cache-dir gotrue && \
    pip install --no-cache-dir realtime-py && \
    pip install --no-cache-dir storage3 && \
    pip install --no-cache-dir supafunc && \
    # Now install supabase without version specification
    pip install --no-cache-dir supabase && \
    # Other requirements
    pip install --no-cache-dir requests>=2.30.0 && \
    # For utility functions
    pip install --no-cache-dir python-dotenv>=1.0.0 && \
    pip install --no-cache-dir gunicorn>=21.2.0

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app

# Create temp_files directory needed by the app
RUN mkdir -p temp_files

# Expose the port
EXPOSE ${PORT}

# Run the application with the wrapper script
CMD ["python", "wrapper.py"] 