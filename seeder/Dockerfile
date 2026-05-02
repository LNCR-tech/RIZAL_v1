FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY [Bb]ackend/requirements.txt /app/backend-requirements.txt
RUN pip install --default-timeout=100 --no-cache-dir -r /app/backend-requirements.txt

COPY [Bb]ackend /backend
COPY seeder /seeder
WORKDIR /seeder

RUN chmod +x /seeder/entrypoint.sh

ENTRYPOINT ["/seeder/entrypoint.sh"]
