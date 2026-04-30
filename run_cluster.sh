#!/bin/bash

echo "Starting Cluster Doc AI..."

# Ensure uploads directory exists
mkdir -p uploads

# Check if MongoDB is running (basic check, assumes localhost:27017)
echo "Checking MongoDB..."
if ! nc -z localhost 27017; then
  echo "WARNING: MongoDB does not seem to be running on localhost:27017. Make sure to start it!"
fi

# Function to stop all background jobs on exit
cleanup() {
    echo "Stopping cluster..."
    kill $(jobs -p)
    exit
}
trap cleanup EXIT

# Install requirements if needed
echo "Installing requirements..."
pip install -r requirements.txt

# Start Machine 1 (Port 8001)
echo "Starting Machine 1 (Lector Profundo)..."
cd machine1
uvicorn main:app --host 0.0.0.0 --port 8001 &
cd ..

# Start Machine 2 (Port 8002)
echo "Starting Machine 2 (Extractor Analítico)..."
cd machine2
uvicorn main:app --host 0.0.0.0 --port 8002 &
cd ..

# Start Machine 3 (Port 8003)
echo "Starting Machine 3 (Sintetizador y Juez)..."
cd machine3
uvicorn main:app --host 0.0.0.0 --port 8003 &
cd ..

# Start Frontend / Gateway (Port 8000)
echo "Starting Frontend Gateway..."
cd frontend
uvicorn main:app --host 0.0.0.0 --port 8000 &
cd ..

echo "Cluster started!"
echo "Access the platform at: http://localhost:8000"
echo "Press Ctrl+C to stop all services."

# Wait for all background jobs
wait
