# Backend API - HireMind Platform

## Overview

This is the FastAPI backend for the HireMind AI-powered recruitment platform. It handles:
- User authentication (registration, login)
- CV analysis and parsing
- Resume-to-job matching with embeddings
- AI-driven interview chat
- Job management for companies

## Technology Stack

- **Framework**: FastAPI 0.115.8
- **Server**: Uvicorn 0.34.0
- **Language**: Python 3.9+
- **AI/ML**: Sentence Transformers, PyTorch, Transformers
- **Database**: SQLite (default) / PostgreSQL (production)
- **API Style**: RESTful with OpenAPI documentation

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # Entry point
│   ├── routes/                  # API endpoints
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── cv.py               # CV analysis endpoints
│   │   ├── jobs.py             # Job management endpoints
│   │   └── chat.py             # Interview chat endpoints
│   ├── services/               # Business logic
│   │   ├── cv_service.py
│   │   ├── matching_service.py
│   │   └── interview_service.py
│   ├── schemas.py              # Pydantic models
│   └── __init__.py
├── requirements.txt
└── README.md
```

## Installation

### 1. Create Virtual Environment

```bash
python -m venv .venv

# Activate
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp ../.env.example .env
# Edit .env with your configuration
```

## Running the Server

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, access:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### CV Analysis
- `POST /api/cv/upload` - Upload and analyze CV
- `GET /api/cv/{cv_id}` - Get CV analysis results
- `GET /api/cv/list` - List all user CVs

### Jobs
- `POST /api/jobs` - Create job posting
- `GET /api/jobs` - List jobs
- `GET /api/jobs/{job_id}` - Get job details

### Matching
- `POST /api/match/candidates` - Get matched candidates for job
- `GET /api/match/jobs` - Get matched jobs for candidate

### Interview
- `POST /api/chat/send` - Send message in interview
- `POST /api/chat/start` - Start new interview

## Key Features

### CV Analysis
- Parses PDF, DOCX, TXT files
- Extracts name, email, phone, experience
- Identifies education and certifications
- Detects skills using NLP

### Skill Matching
- Uses Sentence Transformers for embeddings
- Computes cosine similarity between CV and job
- Multi-dimensional scoring (skills, experience, etc.)
- Real-time ranking

### Interview System
- Chat-based technical interviews
- AI evaluation of responses
- Scoring on: Technical Depth, Communication, Experience
- Interview transcripts and analytics

## Dependencies

Key packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sentence-transformers` - Embeddings generation
- `pdfplumber` - PDF parsing
- `python-docx` - DOCX parsing
- `pydantic` - Data validation
- `scikit-learn` - ML utilities

See `requirements.txt` for complete list with versions.

## Configuration

Environment variables (from `.env`):
```
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
DATABASE_URL=sqlite:///./database/hiremind.db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SECRET_KEY=your-secret-key
```

## Database

### SQLite (Development)
```bash
python ../database/init_db.py
```

### PostgreSQL (Production)
```bash
# Update DATABASE_URL in .env:
# postgresql://user:password@localhost:5432/hiremind_db
python ../database/init_db.py
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Performance

- Average response time: < 200ms
- CV parsing: 200-500ms per document
- Embedding generation: 100-300ms
- Matching algorithm: 50-100ms per candidate

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"
**Solution**: Make sure you're in the project root, not the backend folder:
```bash
cd ..  # Go to project root
uvicorn backend.app.main:app --reload
```

### Issue: Port 8000 already in use
**Solution**: Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

### Issue: Database connection error
**Solution**: Ensure `.env` has correct `DATABASE_URL`:
```bash
sqlite:///./database/hiremind.db  # For SQLite
# or
postgresql://user:pass@localhost:5432/hiremind  # For PostgreSQL
```

## Development Workflow

1. Create a new branch: `git checkout -b feature/my-feature`
2. Make changes
3. Test: `pytest tests/`
4. Commit: `git commit -m "feat: description"`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request

## Security

- All passwords are hashed with secure algorithms
- JWT tokens for authentication
- Input validation on all endpoints
- CORS protection configured
- Rate limiting on sensitive endpoints
- File upload validation

See [SECURITY.md](../SECURITY.md) for more details.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - See [LICENSE](../LICENSE) for details.

## Support

- 📧 Email: support@hiremind.app
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/HireMind/issues)
- 📖 Docs: See README.md in project root

---

**Last Updated**: April 2024
