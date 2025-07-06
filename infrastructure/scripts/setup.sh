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
check_command "pnpm"
check_command "python3"

# Check if Docker is available and running
check_docker() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Find next available port starting from given port
find_available_port() {
    local port=$1
    while lsof -i:$port > /dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}

# Determine setup mode
DOCKER_AVAILABLE=false
if check_docker; then
    DOCKER_AVAILABLE=true
    echo "✅ Docker is available and running"
else
    echo "⚠️  Docker is not available or not running"
    echo "📝 Will set up for local PostgreSQL development"
fi

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

# Set up database based on available tools
if [ "$DOCKER_AVAILABLE" = true ]; then
    # Find available API port
    API_PORT=$(find_available_port 5001)
    echo "🔍 Using API port: $API_PORT"
    
    # Update docker-compose.yml with available port
    sed -i.bak "s/- \"[0-9]*:5000\"/- \"$API_PORT:5000\"/" docker-compose.yml
    sed -i.bak "s/http:\/\/localhost:[0-9]*/http:\/\/localhost:$API_PORT/" docker-compose.yml
    
    # Update Next.js config
    sed -i.bak "s/localhost:[0-9]*/localhost:$API_PORT/" apps/web/next.config.js
    
    echo "🐘 Starting PostgreSQL and Redis with Docker..."
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    sleep 10
    
    # Check if database is accessible
    while ! docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; do
        echo "Waiting for database connection..."
        sleep 2
    done
    
    # Apply schema directly since Alembic has connection issues with Docker
    echo "🗄️ Setting up database schema..."
    docker-compose exec -T postgres psql -U postgres -d takeabreak_dev < database_schema_fixed.sql || echo "⚠️ Schema might already exist"
    
    # Seed initial data
    echo "🌱 Seeding initial data..."
    cd apps/api
    source venv/bin/activate
    python scripts/seed.py || echo "⚠️ Seeding failed - database might already be seeded"
    
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
    echo "  pnpm dev:api   # Backend only (http://localhost:$API_PORT)"
    echo ""
    echo "To stop services:"
    echo "  pnpm stop      # Stop all Docker services"
    
else
    echo "📋 Manual Database Setup Required"
    echo ""
    echo "Since Docker is not available, you'll need to:"
    echo "1. Install PostgreSQL locally:"
    echo "   macOS: brew install postgresql@16"
    echo "   Ubuntu: sudo apt install postgresql-16"
    echo ""
    echo "2. Create database:"
    echo "   createdb takeabreak_dev"
    echo ""
    echo "3. Update connection string in apps/api/.env:"
    echo "   DATABASE_URL=postgresql://[username]:[password]@localhost:5432/takeabreak_dev"
    echo ""
    echo "4. Run migrations:"
    echo "   cd apps/api && source venv/bin/activate"
    echo "   alembic upgrade head"
    echo "   python scripts/seed.py"
    echo ""
    echo "5. Start services manually:"
    echo "   Terminal 1: cd apps/web && pnpm dev"
    echo "   Terminal 2: cd apps/api && source venv/bin/activate && python run.py"
    echo ""
    echo "💡 For the full Docker experience, install Docker Desktop and re-run this script."
fi

echo ""
echo "Happy coding! 🚀"