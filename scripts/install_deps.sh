#!/bin/bash

# Install dependencies for NewClaw

echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "Dependencies installed successfully!"
