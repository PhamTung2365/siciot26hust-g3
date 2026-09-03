FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y opencv-python \
    && pip install --no-cache-dir opencv-python-headless==5.0.0.93

COPY . .

# Create directories
RUN mkdir -p faces_db captures data

# Expose port
EXPOSE 5000

# Run server
CMD ["python3", "web_stream_face.py"]
