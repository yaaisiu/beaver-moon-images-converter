FROM python:3.10-slim

# Install system dependencies for pillow-heif
RUN apt-get update && apt-get install -y \
    libheif-dev \
    libde265-dev \
    x265 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY convert_images.py .

# Create directories for input and output
RUN mkdir -p input-images output

# Set entrypoint
ENTRYPOINT ["python", "convert_images.py"]

