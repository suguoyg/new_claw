#!/bin/bash
# Build and run NewClaw with Docker

set -e

echo "Building NewClaw..."

# Build containers
echo "Building Docker containers..."
docker-compose build

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "=========================================="
echo "NewClaw is running!"
echo "=========================================="
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo "=========================================="
