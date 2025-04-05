FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0

# Expose the port
EXPOSE ${PORT}

# Run the application
CMD ["python", "main.py"] 