# Base image with Java 11 (needed for PySpark)
FROM openjdk:11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.9, pip, and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.9 \
    python3.9-dev \
    python3-pip \
    gcc \
    g++ \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

# Install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install --extra-index-url https://download.pytorch.org/whl/cpu -r /tmp/requirements.txt

# Set working directory to `app/` and copy only that
WORKDIR /app
COPY ./app /app

ENV PYTHONPATH=/app
ENV PORT=8000

# 👇 We are now *inside* the `app` directory, so we can reference app.py as `app`
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
