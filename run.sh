#!/bin/bash
IMAGE_NAME="film-streamer"
PORT=5000

echo "Building Docker image..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "Build failed. Exiting."
    exit 1
fi

echo "Running container on port $PORT..."
docker run -p $PORT:5000 -v $(pwd)/films:/app/films $IMAGE_NAME
