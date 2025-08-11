# Use an official Python 3.12 base image
FROM python:3.12.7-slim

ARG JT_ENCODE_ARG

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JT_ENCODE_ARG=${JT_ENCODE_ARG}

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5010

# Define the entry point
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5010", "--reload"]