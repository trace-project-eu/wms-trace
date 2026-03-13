FROM python:3.10-slim

LABEL authors="savvas-certh"

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Forces logs to print instantly (Fixes the out-of-order log issue!)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (to leverage Docker cache for faster rebuilds)
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose port 5000 so the outside world can talk to Flask
EXPOSE 5000

# Command to run the Flask API
CMD ["python", "app.py"]