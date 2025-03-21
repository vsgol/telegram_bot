#!/bin/bash

# Name of the service
SERVICE_NAME=bot

echo "Building Docker image..."
docker compose build

echo "Cleaning up old containers (if any)..."
docker compose down --remove-orphans

echo "Starting the bot container..."
docker compose up -d

echo "Showing logs:"
docker compose logs -f $SERVICE_NAME
