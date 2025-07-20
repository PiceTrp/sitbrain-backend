# Base image with Python
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# If using pyproject.toml instead of requirements.txt
# COPY pyproject.toml poetry.lock* ./
# RUN pip install poetry && poetry install --no-root

# Copy the whole FastAPI project
COPY . .

# Copy environment file
COPY .env .env

# Expose the port FastAPI will run on
EXPOSE 8080

# Run the app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
