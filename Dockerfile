# Use an official Python runtime as a parent image.
# We'll stick with 3.9 as a stable version that should work well.
FROM python:3.9-slim-buster

# Set the working directory in the container.
# All subsequent commands will be run from this directory inside the container.
WORKDIR /app

# Copy the current directory contents (your Flask app, requirements.txt, etc.)
# into the container at /app.
COPY . /app

# Install any needed dependencies specified in requirements.txt.
# --no-cache-dir reduces the image size by not storing pip's cache.
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your Flask app will run on.
# Cloud Run injects a PORT environment variable, which Gunicorn will listen on.
# We use 8080 here as a common convention for containerized web apps.
ENV PORT 8080
EXPOSE 8080

# Command to run the Flask application using Gunicorn (a production-ready WSGI server).
# 'app:app' assumes your Flask application instance is named 'app' in your 'app.py' file.
# --bind :$PORT tells Gunicorn to listen on the port provided by the environment variable.
# --workers 1 is generally recommended for Cloud Run as it autoscales instances.
# --threads 8 allows the single worker to handle multiple requests concurrently.
# --timeout 0 disables the worker timeout, useful for long-polling (like SocketIO).
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
