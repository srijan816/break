# takeabreak.life

> **Intelligent Wellness for Busy Professionals**

A premium corporate wellness web application that integrates with work calendars to deliver AI-powered break recommendations, helping prevent burnout and boost productivity.

## 🚀 Quick Start

### Prerequisites

**Required:**
- **Node.js** 18+ with **pnpm** 8+
- **Python** 3.11+

**Recommended (for easiest setup):**
- **Docker** and **Docker Compose**

### Setup Options

#### Option 1: Docker Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/srijan816/break.git
cd break

# Make sure Docker is running, then:
./infrastructure/scripts/setup.sh

# Start the application
pnpm dev
```

#### Option 2: Local PostgreSQL Setup

If you don't have Docker, follow these steps:

```bash
# Clone the repository
git clone https://github.com/srijan816/break.git
cd break

# Run setup script (it will detect no Docker and give instructions)
./infrastructure/scripts/setup.sh

# Install PostgreSQL locally
brew install postgresql@16  # macOS
# OR
sudo apt install postgresql-16  # Ubuntu

# Create database
createdb takeabreak_dev

# Set up environment
cd apps/api
cp .env.example .env
# Edit .env to update DATABASE_URL with your local PostgreSQL credentials

# Run migrations and seed data
source venv/bin/activate
alembic upgrade head
python scripts/seed.py

# Start frontend (Terminal 1)
cd ../../apps/web
pnpm dev

# Start backend (Terminal 2)
cd ../api
source venv/bin/activate
python run.py
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:5000
- **Database**: localhost:5432

## 📁 Project Structure

```
takeabreak/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # Flask backend
├── packages/
│   ├── shared/       # Shared types/constants
│   └── ui/           # Shared UI components
├── infrastructure/
│   ├── docker/       # Docker configurations
│   └── scripts/      # Setup and deployment scripts
├── .github/
│   └── workflows/    # CI/CD pipelines
└── docs/             # Documentation
```

## 🛠️ Development

### Starting Services

```bash
# Start all services (recommended)
pnpm dev

# Start individual services
pnpm dev:web    # Frontend only
pnpm dev:api    # Backend only

# Stop all services
pnpm stop
```

### Database Management

```bash
# Run migrations
pnpm db:migrate

# Seed test data
pnpm db:seed

# Reset database (⚠️ destructive)
docker-compose down -v
docker-compose up -d postgres
pnpm db:migrate
pnpm db:seed
```

### Environment Configuration

Copy the example environment files and customize:

```bash
# Frontend
cp apps/web/.env.example apps/web/.env

# Backend
cp apps/api/.env.example apps/api/.env
```

Required environment variables:
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key

## 🏗️ Architecture

### Frontend (Next.js 14)
- **Framework**: Next.js with App Router
- **Styling**: Tailwind CSS with custom design system
- **State**: Zustand for global state
- **Data Fetching**: TanStack Query
- **Authentication**: NextAuth.js

### Backend (Flask)
- **Framework**: Flask with blueprints
- **Database**: PostgreSQL with SQLAlchemy
- **Migrations**: Alembic
- **Authentication**: JWT tokens
- **Background Tasks**: Celery with Redis

### Database Schema
```sql
-- Core tables
users                 # User profiles and preferences
calendar_connections  # OAuth tokens for calendar access
calendar_events       # Cached calendar data
break_sessions        # Content library
break_recommendations # AI suggestions
completed_breaks      # User activity tracking
user_streaks         # Motivation metrics
company_analytics    # Aggregated insights
```

## 🔐 Security

- **Privacy First**: Individual data never shared with employers
- **Row-Level Security**: Database-level data isolation
- **Encrypted Tokens**: OAuth tokens encrypted at rest
- **CORS Protection**: Strict origin controls
- **Input Validation**: Comprehensive sanitization

## 🧪 Testing

```bash
# Frontend tests
cd apps/web
pnpm test

# Backend tests
cd apps/api
source venv/bin/activate
pytest

# E2E tests
pnpm test:e2e
```

## 📦 Deployment

### Environment Setup

1. **Production Environment Variables**
   ```bash
   # Set in production
   FLASK_ENV=production
   DATABASE_URL=postgresql://...
   SECRET_KEY=<secure-random-key>
   JWT_SECRET_KEY=<secure-random-key>
   ```

2. **Frontend Deployment (Vercel)**
   ```bash
   # Connect to Vercel
   npx vercel --cwd apps/web
   ```

3. **Backend Deployment (Docker)**
   ```bash
   # Build production image
   docker build -f infrastructure/docker/Dockerfile.api -t takeabreak-api .
   ```

## 🎯 MVP Features

### ✅ Phase 1 (Current)
- [x] Project scaffolding
- [x] Database schema
- [x] Docker environment
- [x] Basic authentication endpoints

### 🚧 Phase 2 (Next)
- [ ] Google Calendar integration
- [ ] Break recommendation algorithm
- [ ] Session player
- [ ] Dashboard UI

### 📋 Phase 3 (Future)
- [ ] Streak tracking
- [ ] Company analytics
- [ ] Mobile responsiveness
- [ ] Performance optimization

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pnpm test`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- **Code Style**: ESLint + Prettier for frontend, Black + Flake8 for backend
- **Commits**: Use conventional commit format
- **Testing**: Maintain >80% code coverage
- **Documentation**: Update docs for new features

## 📚 API Documentation

API documentation is available at:
- **Development**: http://localhost:5000/docs
- **Swagger UI**: Auto-generated from OpenAPI spec

### Core Endpoints

```
POST /api/v1/auth/google     # Google OAuth
GET  /api/v1/dashboard       # Dashboard data
GET  /api/v1/sessions        # Break library
POST /api/v1/breaks/start    # Start session
POST /api/v1/calendar/sync   # Sync calendar
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker not running error**
   ```bash
   # Start Docker Desktop or install Docker
   # Then re-run: ./infrastructure/scripts/setup.sh
   
   # Alternative: Use local PostgreSQL setup (see Option 2 above)
   ```

2. **Port conflicts**
   ```bash
   # Check what's using ports
   lsof -i :3000
   lsof -i :5000
   
   # Kill processes if needed
   kill -9 $(lsof -t -i:3000)
   ```

3. **Database connection errors**
   ```bash
   # For Docker setup:
   docker-compose restart postgres
   docker-compose logs postgres
   
   # For local PostgreSQL:
   brew services restart postgresql@16  # macOS
   sudo systemctl restart postgresql    # Ubuntu
   ```

4. **Python virtual environment issues**
   ```bash
   # Recreate venv
   cd apps/api
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Alembic migration errors**
   ```bash
   # Reset database (⚠️ destructive)
   cd apps/api
   source venv/bin/activate
   
   # For Docker:
   docker-compose down -v postgres
   docker-compose up -d postgres
   
   # For local PostgreSQL:
   dropdb takeabreak_dev
   createdb takeabreak_dev
   
   # Then run migrations:
   alembic upgrade head
   python scripts/seed.py
   ```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/srijan816/break/issues)
- **Discussions**: [GitHub Discussions](https://github.com/srijan816/break/discussions)
- **Email**: support@takeabreak.life

## 📄 License

This project is proprietary software. All rights reserved.

---

**Built with ❤️ for busy professionals who deserve better wellness at work.**