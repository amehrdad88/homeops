FROM python:3.12-alpine

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install system dependencies (minimal, but needed for requests/ssl)
RUN apk add --no-cache \
    ca-certificates \
    gcc \
    musl-dev \
    libffi-dev

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Expose the port Home Assistant ingress expects
EXPOSE 8000

# Start the app
CMD ["python", "server.py"]