# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

takeabreak.life is a premium corporate wellness web application built as a **monorepo** with Next.js 15 frontend and Flask backend. The app integrates with work calendars to deliver AI-powered break recommendations, helping prevent burnout and boost productivity.

## Development Commands

### Quick Start
```bash
# One-command setup (requires Docker)
./infrastructure/scripts/setup.sh
pnpm dev

# Manual database setup if Docker issues
docker-compose exec -T postgres psql -U postgres -d takeabreak_dev < database_schema_fixed.sql
docker-compose exec -T postgres psql -U postgres -d takeabreak_dev < seed_data.sql
```

### Daily Development
```bash
# Start all services
pnpm dev                    # Docker + all services
pnpm dev:local              # Local services only

# Individual services  
pnpm dev:web               # Frontend only (port 3000)
pnpm dev:api               # Backend only (port 5000)

# Database operations
pnpm db:migrate            # Run Alembic migrations
pnpm db:seed               # Seed initial break content
pnpm db:setup              # Migrate + seed in one command

# Testing
pnpm test                  # All tests
cd apps/web && pnpm test   # Frontend tests only
cd apps/api && source venv/bin/activate && pytest  # Backend tests only
```

### Database Troubleshooting
```bash
# Reset database completely (Docker)
docker-compose down -v postgres
docker-compose up -d postgres
docker-compose exec -T postgres psql -U postgres -d takeabreak_dev < database_schema_fixed.sql
docker-compose exec -T postgres psql -U postgres -d takeabreak_dev < seed_data.sql

# Check database connection
docker-compose exec postgres psql -U postgres -d takeabreak_dev -c "SELECT COUNT(*) FROM break_sessions;"
```

## Architecture Overview

### Monorepo Structure
- **apps/web/** - Next.js 15 frontend with App Router, TypeScript, Tailwind CSS
- **apps/api/** - Flask backend with SQLAlchemy, Alembic migrations, Celery background tasks
- **packages/shared/** - Shared types and constants (future use)
- **infrastructure/** - Docker configs, setup scripts, deployment files

### Backend Architecture (Flask)
- **Application Factory Pattern**: `app/__init__.py` creates Flask app with extensions
- **Blueprint Organization**: Routes organized in `auth/`, `breaks/`, `calendar/` modules
- **Models**: SQLAlchemy models in `app/models/` with relationships:
  - **User** → CalendarConnection, CalendarEvent, CompletedBreak, UserStreak
  - **BreakSession** → BreakRecommendation, CompletedBreak
  - **CalendarEvent** ← User (calendar analysis for break suggestions)
- **Configuration**: Environment-based config in `config.py` (dev/test/prod)

### Frontend Architecture (Next.js 15)
- **App Router**: Modern Next.js 15 routing in `src/app/`
- **Design System**: Custom Tailwind config with takeabreak.life brand colors (teal primary, warm sand secondary)
- **State Management**: Zustand for global state (when implemented)
- **Data Fetching**: TanStack Query for server state
- **Authentication**: NextAuth.js integration planned

### Database Schema Key Points
- **Privacy-First Design**: User data completely isolated from company analytics
- **Calendar Integration**: OAuth tokens stored encrypted, events cached for analysis
- **Break Tracking**: Recommendations → Completed breaks → Streak calculation
- **Extensible**: Schema supports future features (team breaks, advanced analytics)

### MVP Feature Flow
1. **User onboarding**: OAuth → calendar permission → preferences
2. **Calendar analysis**: Background sync → meeting detection → gap finding
3. **Break recommendations**: AI algorithm → time/type matching → notifications
4. **Break experience**: Session player → completion tracking → streak updates

## Key Configuration

### Environment Variables (Critical)
```bash
# Backend (.env in apps/api/)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/takeabreak_dev
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-secret
SECRET_KEY=flask-secret-key
JWT_SECRET_KEY=jwt-signing-key

# Frontend (.env in apps/web/)
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=nextauth-secret
```

### Application Constants (apps/api/config.py)
- `BREAKS_PER_DAY_LIMIT = 3` - Max AI suggestions per day
- `MIN_BREAK_GAP_MINUTES = 15` - Minimum calendar gap for break suggestions
- `SYNC_INTERVAL_MINUTES = 5` - Calendar sync frequency

### Database Connection Notes
- **Docker setup**: PostgreSQL runs in container, connected via docker-compose network
- **Local setup**: Direct PostgreSQL connection to localhost:5432
- **Migration issues**: Use `database_schema_fixed.sql` directly if Alembic fails (common during Docker setup)

## Development Workflow Notes

### Docker vs Local Development
- **Docker (Recommended)**: Full environment with PostgreSQL + Redis containers
- **Local fallback**: If Docker issues, use local PostgreSQL + manual service startup
- **Database seeding**: Always ensure break_sessions table has 5 MVP sessions

### Backend Development
- **Virtual environment**: Always activate `apps/api/venv` before running Python commands
- **Blueprints**: Add new routes to existing blueprints in `app/auth/`, `app/breaks/`, `app/calendar/`
- **Models**: Use SQLAlchemy relationships, follow existing pattern for new models
- **Migrations**: Create via `alembic revision --autogenerate` when schema changes

### Frontend Development  
- **Component patterns**: Follow existing structure in `src/app/`, use Tailwind classes
- **API integration**: Use TanStack Query for server communication
- **Design system**: Leverage pre-configured Tailwind theme for brand consistency