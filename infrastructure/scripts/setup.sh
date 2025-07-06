#!/bin/bash

# takeabreak.life Development Setup Script
set -e

echo "🚀 Setting up takeabreak.life development environment..."

# Check for required tools
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 is required but not installed."
        echo "Please install $1 and run this script again."
        exit 1
    fi
}

echo "📋 Checking required tools..."
check_command "docker"
check_command "docker-compose"
check_command "pnpm"
check_command "python3"

# Set up frontend
echo "📦 Setting up frontend dependencies..."
cd apps/web
cp .env.example .env
pnpm install
cd ../..

# Set up backend
echo "🐍 Setting up backend environment..."
cd apps/api

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

cd ../..

# Set up database with Docker
echo "🐘 Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🗄️ Running database migrations..."
cd apps/api
source venv/bin/activate
alembic upgrade head

# Seed initial data
echo "🌱 Seeding initial data..."
python scripts/seed.py

cd ../..

echo "✅ Setup complete!"
echo ""
echo "🎉 Your takeabreak.life development environment is ready!"
echo ""
echo "To start the application:"
echo "  pnpm dev       # Start all services"
echo ""
echo "Individual services:"
echo "  pnpm dev:web   # Frontend only (http://localhost:3000)"
echo "  pnpm dev:api   # Backend only (http://localhost:5000)"
echo ""
echo "To stop services:"
echo "  pnpm stop      # Stop all Docker services"
echo ""
echo "Happy coding! 🚀"