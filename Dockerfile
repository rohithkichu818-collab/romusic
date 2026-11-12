FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (ffmpeg for crystal-clear audio extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Initialize and seed database
RUN python seed_data.py

# Default port
ENV PORT=8000
EXPOSE 8000

# Start WSGI server
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
