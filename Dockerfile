# Use Google's official Python image from the Cloud SDK
# This includes Python, pip, and other utilities.
#FROM gcr.io/google-appengine/python

# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /workspace

# Copy local code to the container image
COPY . .

# Set environment variables for Flask
ENV FLASK_ENV=production \
    FLASK_APP=app.py

# Install system dependencies required for common Python packages
RUN apt-get update -y && apt-get install -y \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev

# Install Python dependencies
RUN pip install -r requirements.txt

# Run the application using gunicorn
CMD gunicorn -b :$PORT app:app --timeout 120
