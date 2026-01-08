FROM python:3.12-alpine

# Ensure Python logs are unbuffered so that logs appear in the add‑on log output immediately
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies required for building Python packages on Alpine
RUN apk add --no-cache \
    ca-certificates \
    gcc \
    musl-dev \
    libffi-dev

# Copy Python dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the internal port used by Home Assistant ingress
EXPOSE 8099

# Start the Flask application
CMD ["python", "app/main.py"]