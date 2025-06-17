FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy team files
COPY . .

# Create logs directory
RUN mkdir -p /logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8090

# Expose port
EXPOSE 8090

# Run the server
CMD ["python", "team_server.py"]
