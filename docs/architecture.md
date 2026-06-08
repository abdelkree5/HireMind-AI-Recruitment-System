# System Architecture

## Overview

HireMind is a modern AI-powered recruitment system with a distributed architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
├─────────────────────────────────────────────────────────────┤
│  React Frontend (Candidate & Company Portals)                │
│  - Component-based UI                                        │
│  - Tailwind CSS styling                                      │
│  - React Router for navigation                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    HTTP/REST API
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Application Layer                           │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                             │
│  - Authentication (JWT)                                      │
│  - API Routes (Auth, CV, Jobs, Chat)                         │
│  - Business Logic Services                                   │
│  - CORS & Security                                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  AI Engine   │  │  Database    │  │   Cache      │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ • Parser     │  │ PostgreSQL/  │  │ Redis        │
│ • Embeddings │  │   SQLite     │  │ (Optional)   │
│ • Matcher    │  │ • Users      │  │ • Sessions   │
│ • Interview  │  │ • CVs        │  │ • Cache      │
│              │  │ • Jobs       │  │              │
│              │  │ • Interviews │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Components

### 1. Frontend (React)

**Technology Stack:**

- React 18.3.1
- React Router 7.14.1
- Tailwind CSS 3.4.17
- Vite 6.4.2

**Key Features:**

- Responsive design
- Real-time updates
- Role-based UI (Candidate/Company)
- Chat interface for interviews
- Dashboard with analytics

**Structure:**

```
src/
├── pages/          # Page components
├── components/     # Reusable components
├── layout/         # Layout wrappers
├── api/            # API client
└── styles/         # CSS stylesheets
```

### 2. Backend (FastAPI)

**Technology Stack:**

- FastAPI 0.115.8
- Uvicorn ASGI server
- Pydantic for validation
- SQLAlchemy for ORM

**Key Routes:**

- `/api/auth/` - Authentication
- `/api/cv/` - CV management
- `/api/jobs/` - Job management
- `/api/match/` - Matching engine
- `/api/chat/` - Interview chat

**Features:**

- JWT authentication
- CORS protection
- Rate limiting
- Input validation
- Error handling
- Auto-generated API docs (Swagger UI)

**Structure:**

```
backend/app/
├── main.py         # Entry point
├── routes/         # API endpoints
├── services/       # Business logic
├── schemas.py      # Pydantic models
└── __init__.py
```

### 3. AI Engine

**Technology Stack:**

- Sentence Transformers 3.4.1
- PyTorch 2.4.0+
- Transformers 4.48.2
- scikit-learn 1.6.1

**Components:**

#### Parser (`parser.py`)

- PDF extraction (pdfplumber)
- DOCX parsing (python-docx)
- Text cleaning and normalization

#### Skill Extractor (`skills.py`)

- NLP-based skills detection
- Pattern matching
- Skill categorization

#### Embeddings (`embeddings.py`)

- Generates vector embeddings
- Uses `all-MiniLM-L6-v2` model by default
- Supports custom models

#### Matcher (`matcher.py`)

- Cosine similarity calculation
- Multi-dimensional scoring
- Ranking algorithm

#### Interview (`interview.py`)

- Question generation
- Response evaluation
- Scoring logic

### 4. Database

**Options:**

- **Development:** SQLite (portable, zero-config)
- **Production:** PostgreSQL (recommended)

**Schema:**

```
Users
├── id
├── email
├── role (candidate/company)
└── auth data

CVs
├── id
├── user_id
├── file_path
└── parsed_data

Jobs
├── id
├── company_id
├── title
├── requirements
└── embedding

Applications
├── id
├── candidate_id
├── job_id
└── status

Interviews
├── id
├── candidate_id
├── job_id
└── chat_history
```

## Data Flow

### CV Analysis Flow

```
1. User uploads CV
   ↓
2. Parse document (PDF/DOCX/TXT)
   ↓
3. Extract text & information
   ↓
4. Generate embeddings
   ↓
5. Store in database
   ↓
6. Return results to frontend
```

### Job Matching Flow

```
1. Jobs posted with requirements
   ↓
2. Generate job embeddings
   ↓
3. For each candidate CV:
   a) Calculate cosine similarity
   b) Score skill match
   c) Evaluate experience
   ↓
4. Rank candidates by score
   ↓
5. Display results
```

### Interview Flow

```
1. Start interview session
   ↓
2. AI generates questions
   ↓
3. Candidate submits answers
   ↓
4. AI evaluates response
   ↓
5. Accumulate score
   ↓
6. Save to database
   ↓
7. Display final score
```

## Performance Considerations

### Frontend

- **Build:** < 30 seconds with Vite
- **Bundle Size:** 19.6 KB CSS + 236 KB JS (gzipped)
- **Load Time:** < 1 second initial load
- **Runtime:** < 100ms page transitions

### Backend

- **Response Time:** < 200ms median
- **Concurrent Users:** 100+ with uvicorn workers
- **CV Parsing:** 200-500ms per document
- **Embeddings:** 100-300ms per CV
- **Matching:** 50-100ms per candidate

### Database

- **Query Time:** < 50ms for indexed queries
- **Connections:** 20+ concurrent connections
- **Schema:** Optimized with indexes

## Security Architecture

### Authentication

- JWT tokens (HS256)
- Token expiration (30 minutes)
- Refresh tokens

### Data Protection

- Password hashing (bcrypt)
- Input validation (Pydantic)
- SQL injection prevention
- CORS configuration

### Infrastructure

- HTTPS enforced
- Rate limiting
- CSRF protection
- Secure cookie handling

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│         Docker Containers               │
├─────────────────────────────────────────┤
│                                         │
│  Frontend (Nginx)   Backend (Uvicorn)   │
│  :80                :8000               │
│                                         │
│  Database (PostgreSQL)                  │
│  :5432                                  │
│                                         │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│      Load Balancer / Reverse Proxy      │
│      (Nginx / HAProxy)                  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Cloud Platform / VPS                  │
│   (AWS/Azure/DigitalOcean/Heroku)       │
└─────────────────────────────────────────┘
```

## Scalability

### Horizontal Scaling

- Multiple backend instances
- Database replication
- Load balancing

### Vertical Scaling

- Increased server resources
- GPU support for embeddings
- Database optimization

### Caching Strategy

- Redis for session management
- Browser caching for static assets
- API response caching

## Monitoring & Logging

**Metrics:**

- Request/response times
- Error rates
- Active users
- API usage

**Logging:**

- Application logs
- Database queries
- API requests
- System events

## Future Enhancements

- [ ] WebSocket for real-time updates
- [x] Event-driven agent workflow with RabbitMQ (see `docs/rabbitmq_event_architecture.md`)
- [ ] Advanced search (Elasticsearch)
- [ ] Caching layer (Redis)
- [ ] Multi-tenancy support
- [ ] Advanced analytics

---

**Last Updated:** June 2026
