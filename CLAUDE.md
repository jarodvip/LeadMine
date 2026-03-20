# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeadMine (线索矿工) is a hot news collection and sales lead mining system. It automatically scrapes news from multiple sources (36kr, 虎嗅, 创头条, RSS feeds, WeChat official accounts via RSSHub), processes articles using NLP, extracts business leads, and enriches them with company information.

## Technology Stack

- **Backend**: Python 3.11 + FastAPI (async)
- **Database**: MySQL 8.0 + Redis 7
- **Search**: Elasticsearch 8.12 (optional)
- **Frontend**: Vue 3 + Element Plus + Vite
- **Scraping**: Scrapy 2.11 + Playwright + RSSHub
- **Deployment**: Docker + Docker Compose + Nginx

## Project Structure

```
LeadMine/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes (auth, leads, articles, sources, users, alerts)
│   │   ├── core/          # Config, database, security, logging, caching, rate limiting
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic validation schemas
│   │   ├── services/      # Business logic services
│   │   ├── processors/    # Data processing pipeline (NLP, lead extraction, deduplication)
│   │   ├── middleware/    # Rate limiting, caching middleware
│   │   └── main.py        # FastAPI entry point
│   ├── scrapers/          # Web scrapers (36kr, huxiu, tmt, cyzone)
│   └── tests/             # Test suite
├── web/                   # Vue 3 frontend (port 8501)
├── docker-compose.yml     # Local development
├── docker-compose.prod.yml
└── nginx/                 # Nginx config with HTTPS
```

## Commands

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd web
npm install
npm run dev      # Development server on port 8501
npm run build    # Production build
```

### Docker
```bash
docker-compose up -d              # Start all services
docker-compose ps                 # Check status
docker-compose logs -f backend    # View backend logs
docker-compose down               # Stop services
```

### Testing
```bash
cd backend
pytest                            # Run all tests
pytest tests/processors/          # Run processor tests only
pytest tests/security/            # Run security tests
pytest -m "not slow"              # Skip slow tests
```

## Database

Core tables: `articles`, `leads`, `users`, `data_sources`, `alerts`, `notifications`

Key enums:
- `LeadEventTypeEnum`: financing, acquisition, product, expansion, procurement, executive, policy
- `LeadStatusEnum`: new, contacted, converted, invalid
- `UserRoleEnum`: admin, user, sales, viewer

## API Endpoints

Prefix: `/api/v1`

- **Auth**: `POST /auth/login`, `POST /auth/register`, `GET /auth/me`
- **Leads**: `GET/POST /leads`, `GET/PATCH/DELETE /leads/{id}`, `GET /leads/stats/dashboard`
- **Articles**: `GET /articles`, `GET /articles/{id}`
- **Sources**: `GET/POST /sources`, `PATCH/DELETE /sources/{id}`, `POST /sources/{id}/crawl`
- **Users**: `GET/POST /users`, `PATCH/DELETE /users/{id}` (admin only)
- **Alerts**: `GET/POST /alerts`
- **Processor**: `POST /processor/articles/{id}/process`, `POST /processor/leads/{id}/enrich`

## Configuration

Environment variables (see `.env.example`):
- `DATABASE_URL` - MySQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - JWT signing key (required)
- `ADMIN_PASSWORD` - Initial admin password
- `SMTP_*` / `WEBHOOK_*` - Notification settings
- `AIQICHA_*` - Optional company info API credentials

## Architecture Patterns

1. **Layered Architecture**: API routes → Services → Processors → Database
2. **Async/Await**: FastAPI async endpoints with APScheduler for background tasks
3. **Processor Pipeline**: Article → Cleaner → NLP Processor → Lead Extractor → Deduplicator → Enricher
4. **Spider Factory**: Factory pattern for managing multiple scrapers

## Default Credentials

- Username: `admin`
- Password: `admin123`

## API Documentation

Available at `http://localhost:8000/docs` (Swagger UI)
