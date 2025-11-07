# Using a slim version for a smaller base image
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    libmagic1 \
    libpq-dev \
    swig \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Increase timeout to wait for the new installation
RUN pip install --no-cache-dir -r requirements.txt --timeout 200

COPY src /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
