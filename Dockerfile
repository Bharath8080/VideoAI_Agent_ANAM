# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# build-essential and curl are often needed. 
# You might need additional libraries for audio processing (portaudio19-dev) since I see 'soundfile' and 'SpeechRecognition' in requirements.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make the start script executable
RUN chmod +x start.sh

# Expose ports for Backend (8000) and Frontend (8501)
EXPOSE 8000
EXPOSE 8501

# Run the start script
CMD ["./start.sh"]
