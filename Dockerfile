FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=False

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/

# Convert UTF-16LE requirements file to UTF-8 and install dependencies
RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*
RUN iconv -f UTF-16LE -t UTF-8 requirements.txt > requirements_utf8.txt || cp requirements.txt requirements_utf8.txt
RUN pip install --upgrade pip && \
    pip install -r requirements_utf8.txt && \
    pip install gunicorn whitenoise

# Copy project
COPY . /app/

# Ensure entrypoint is executable and has linux line endings
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
