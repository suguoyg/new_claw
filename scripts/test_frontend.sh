#!/bin/bash
# Frontend build test

echo "Testing frontend build..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Type check
echo "Running TypeScript type check..."
npx vue-tsc --noEmit 2>&1 || {
    echo "TypeScript check failed"
    exit 1
}

# Build
echo "Building frontend..."
npm run build 2>&1 || {
    echo "Build failed"
    exit 1
}

echo "Frontend build test passed!"
