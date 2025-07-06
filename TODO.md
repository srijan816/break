# takeabreak.life MVP Development TODO

## Project Setup & Infrastructure

### 1. Repository Structure
- [ ] Initialize Git repository with `.gitignore` for Node.js and Python
- [ ] Create monorepo structure:
  ```
  takeabreak/
  ├── apps/
  │   ├── web/          # Next.js frontend
  │   └── api/          # Flask backend
  ├── packages/
  │   ├── shared/       # Shared types/constants
  │   └── ui/           # Shared UI components
  ├── infrastructure/
  │   ├── docker/
  │   └── scripts/
  ├── .github/
  │   └── workflows/
  ├── package.json      # Root package.json
  ├── pnpm-workspace.yaml
  └── README.md
  ```

### 2. Frontend Setup (Next.js)
- [ ] Initialize Next.js 14 app with TypeScript:
  ```bash
  cd apps/web
  npx create-next-app@latest . --typescript --tailwind --app
  ```
- [ ] Install core dependencies:
  - [ ] `@tanstack/react-query` for data fetching
  - [ ] `zustand` for state management
  - [ ] `framer-motion` for animations
  - [ ] `next-auth` for authentication
  - [ ] `react-hook-form` + `zod` for forms
  - [ ] `date-fns` for date manipulation
- [ ] Configure environment variables structure (.env.example)
- [ ] Set up path aliases in `tsconfig.json`
- [ ] Create base layout with design system colors

### 3. Backend Setup (Flask)
- [ ] Create Python virtual environment:
  ```bash
  cd apps/api
  python -m venv venv
  source venv/bin/activate  # or venv\Scripts\activate on Windows
  ```
- [ ] Create `requirements.txt` with core dependencies:
  - [ ] Flask
  - [ ] Flask-RESTful
  - [ ] Flask-CORS
  - [ ] SQLAlchemy
  - [ ] psycopg2-binary
  - [ ] python-jose[cryptography] (JWT)
  - [ ] google-auth
  - [ ] google-auth-oauthlib
  - [ ] google-auth-httplib2
  - [ ] google-api-python-client
  - [ ] celery
  - [ ] redis
  - [ ] python-dotenv
- [ ] Create Flask app structure:
  ```
  api/
  ├── app/
  │   ├── __init__.py
  │   ├── auth/
  │   ├── calendar/
  │   ├── breaks/
  │   ├── models/
  │   └── utils/
  ├── migrations/
  ├── tests/
  ├── config.py
  └── run.py
  ```
- [ ] Set up Flask application factory pattern
- [ ] Configure CORS and security headers

### 4. Database Setup
- [ ] Install PostgreSQL locally or use Docker
- [ ] Create development database: `takeabreak_dev`
- [ ] Set up Alembic for migrations:
  ```bash
  alembic init migrations
  ```
- [ ] Create initial migration from schema.sql
- [ ] Seed MVP break content (5 sessions)
- [ ] Set up database connection pooling

### 5. Authentication Implementation
- [ ] Configure Google OAuth 2.0:
  - [ ] Create project in Google Cloud Console
  - [ ] Enable Calendar API
  - [ ] Create OAuth 2.0 credentials
  - [ ] Add redirect URIs
- [ ] Implement JWT token management:
  - [ ] Access token generation
  - [ ] Refresh token rotation
  - [ ] Token validation middleware
- [ ] Create auth endpoints:
  - [ ] `/auth/google` - OAuth flow
  - [ ] `/auth/refresh` - Token refresh
  - [ ] `/auth/logout` - Session cleanup

### 6. Core Features Implementation

#### 6.1 Calendar Integration
- [ ] Implement Google Calendar service:
  - [ ] OAuth token management
  - [ ] Fetch events for next 7 days
  - [ ] Parse and categorize meetings
  - [ ] Store in `calendar_events` table
- [ ] Create sync job with Celery:
  - [ ] Run every 5 minutes during work hours
  - [ ] Handle API rate limits
  - [ ] Update event changes

#### 6.2 Break Recommendation Algorithm
- [ ] Implement core algorithm:
  ```python
  def suggest_break(user_id: str) -> BreakRecommendation:
      # 1. Get user's calendar events
      # 2. Find gaps >= 15 minutes
      # 3. Score opportunities
      # 4. Select best time
      # 5. Match break type
  ```
- [ ] Create recommendation endpoint
- [ ] Schedule daily recommendation generation

#### 6.3 Dashboard API
- [ ] Create dashboard data aggregation:
  - [ ] Dynamic greeting based on time
  - [ ] Current streak calculation
  - [ ] Weekly stats
  - [ ] Today's recommendation
- [ ] Optimize with single query where possible

#### 6.4 Session Player
- [ ] Upload MVP content to S3/CDN:
  - [ ] 5-min breathing exercise (audio)
  - [ ] 10-min meditation (audio)
  - [ ] 5-min desk stretches (video)
  - [ ] 2-min eye rest (audio)
  - [ ] 15-min power nap (audio)
- [ ] Create streaming endpoints
- [ ] Implement session tracking

### 7. Frontend Implementation

#### 7.1 Authentication Flow
- [ ] Create login page with Google OAuth button
- [ ] Implement NextAuth.js configuration
- [ ] Create auth context/hooks
- [ ] Add route protection

#### 7.2 Dashboard Page
- [ ] Create dashboard layout matching mockup
- [ ] Implement real-time greeting
- [ ] Build recommendation card component
- [ ] Add streak display
- [ ] Create "Start Break" interaction

#### 7.3 Session Player
- [ ] Build full-screen player component
- [ ] Implement audio/video playback
- [ ] Add play/pause controls
- [ ] Create exit flow
- [ ] Add completion tracking

#### 7.4 Break Library
- [ ] Create simple grid layout
- [ ] Display 5 MVP sessions
- [ ] Show duration badges
- [ ] Link to session player

### 8. DevOps & CI/CD

#### 8.1 Docker Configuration
- [ ] Create Dockerfile for Next.js app
- [ ] Create Dockerfile for Flask API
- [ ] Create docker-compose.yml for local development
- [ ] Include PostgreSQL and Redis services

#### 8.2 GitHub Actions
- [ ] Create workflow for frontend:
  - [ ] Install dependencies
  - [ ] Run TypeScript checks
  - [ ] Run ESLint
  - [ ] Build production bundle
- [ ] Create workflow for backend:
  - [ ] Install dependencies
  - [ ] Run pytest
  - [ ] Run flake8
  - [ ] Check migrations
- [ ] Add branch protection rules

#### 8.3 Deployment Preparation
- [ ] Set up Vercel project for frontend
- [ ] Choose backend hosting (AWS EC2/ECS or GCP Cloud Run)
- [ ] Configure environment variables
- [ ] Set up monitoring (Sentry)

### 9. Testing

#### 9.1 Backend Testing
- [ ] Unit tests for recommendation algorithm
- [ ] Integration tests for auth flow
- [ ] API endpoint tests
- [ ] Mock external services (Google Calendar)

#### 9.2 Frontend Testing
- [ ] Component tests for key UI elements
- [ ] Integration tests for auth flow
- [ ] E2E test for core user journey

### 10. Security & Performance

#### 10.1 Security
- [ ] Implement rate limiting on API
- [ ] Add input validation on all endpoints
- [ ] Set up HTTPS everywhere
- [ ] Configure CSP headers
- [ ] Encrypt sensitive data (tokens)

#### 10.2 Performance
- [ ] Add Redis caching for dashboard data
- [ ] Implement database query optimization
- [ ] Set up CDN for static assets
- [ ] Configure image optimization

### 11. MVP Polish

#### 11.1 Error Handling
- [ ] Create friendly error pages
- [ ] Add loading states everywhere
- [ ] Implement offline detection
- [ ] Add retry mechanisms

#### 11.2 Analytics
- [ ] Set up privacy-compliant analytics
- [ ] Track core metrics:
  - [ ] Sign-ups
  - [ ] Break completions
  - [ ] Streak retention
- [ ] Create admin dashboard for company stats

### 12. Pre-Launch Checklist
- [ ] Security audit
- [ ] Performance testing (load testing)
- [ ] Cross-browser testing
- [ ] Mobile responsiveness check
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Legal pages (Privacy Policy, Terms)
- [ ] Set up customer support email
- [ ] Create onboarding documentation

## Timeline Estimate

**Week 1-2**: Project setup, authentication, database
**Week 3-4**: Calendar integration, recommendation algorithm
**Week 5-6**: Frontend implementation, session player
**Week 7**: Testing, security, performance
**Week 8**: Polish, deployment, launch prep

Total: 8 weeks for MVP with a small team (2-3 developers)