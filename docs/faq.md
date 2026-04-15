# Frequently Asked Questions (FAQ)

## Getting Started

### Q: How do I install HireMind?

**A:** There are two ways:

1. **Docker (Recommended):**
```bash
docker-compose up
```

2. **Local Setup:**
```bash
# Setup backend
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload

# Setup frontend (new terminal)
cd frontend && npm install && npm run dev
```

### Q: What are the system requirements?

**A:** 
- Python 3.9+
- Node.js 16+
- PostgreSQL (optional, SQLite works for development)
- 2GB RAM minimum
- 500MB disk space (without models)

### Q: How do I access the application?

**A:**
- Frontend: http://localhost:5173
- Backend API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Development

### Q: How do I run tests?

**A:**
```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend
```

### Q: How do I add a new API endpoint?

**A:**
1. Create a new route file in `backend/app/routes/`
2. Define your endpoint with FastAPI decorators
3. Add it to the main router in `backend/app/main.py`
4. Add Pydantic models in `backend/app/schemas.py`

Example:
```python
from fastapi import APIRouter
from backend.app.schemas import MyRequest, MyResponse

router = APIRouter(prefix="/api/myroute", tags=["myroute"])

@router.post("/", response_model=MyResponse)
async def create_item(request: MyRequest):
    return MyResponse(message="Success")
```

### Q: How do I modify the database schema?

**A:**
1. Update the schema in `database/schema.sql`
2. Run migrations: `make db-migrate`
3. Or reinitialize: `python database/init_db.py`

### Q: How do I change Tailwind styling?

**A:**
1. Edit `frontend/tailwind.config.js` for theme
2. Edit `frontend/src/index.css` for custom styles
3. Rebuild: `npm run build:css`

---

## Deployment

### Q: How do I deploy to production?

**A:** See [DEPLOYMENT.md](../DEPLOYMENT.md) for detailed guides on:
- Traditional servers (Ubuntu/Debian)
- Docker deployment
- Cloud platforms (AWS, Heroku, Railway, etc.)

### Q: What's the recommended database for production?

**A:** PostgreSQL is recommended. Update your `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hiremind_db
```

### Q: Do I need a GPU?

**A:** No, but it speeds up embeddings:
- CPU: 100-300ms per CV
- GPU: 20-50ms per CV

To enable GPU:
```env
EMBEDDING_DEVICE=cuda
```

---

## Features

### Q: What file formats does CV upload support?

**A:**
- PDF (.pdf)
- Word (.docx, .doc)
- Text (.txt)

Maximum file size: 10 MB

### Q: How accurate is the AI matching?

**A:**
- Accuracy depends on CV quality and job descriptions
- Typical accuracy: 75-90%
- Improves with fine-tuned models (advanced setup)

### Q: Can I customize the matching algorithm?

**A:** Yes! Modify `ai_engine/matcher.py` for custom scoring logic. You can:
- Adjust weight of different factors
- Add custom scoring rules
- Integrate external APIs

### Q: How many candidates can I match at once?

**A:**
- No hard limit
- Typical: 100+ candidates in real-time
- For 1000+ use batch processing

---

## Troubleshooting

### Q: Port already in use error

**A:** Change the port:
```bash
# Backend
uvicorn backend.app.main:app --port 8001

# Frontend
cd frontend && npm run dev -- --port 3000
```

### Q: Database connection error

**A:** 
1. Check `.env` DATABASE_URL
2. Verify PostgreSQL is running: `psql -U postgres`
3. Reset SQLite: `rm database/hiremind.db && python database/init_db.py`

### Q: Frontend won't connect to backend

**A:**
1. Check backend is running on 8000
2. Check `.env` VITE_API_BASE_URL is correct
3. Check CORS in backend settings
4. Try: `curl http://127.0.0.1:8000/health`

### Q: npm install fails

**A:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Q: Python imports failing

**A:**
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt --force-reinstall
```

### Q: "Module not found" errors

**A:**
```bash
# Run from project root, not subfolder
cd e:\graduate\Ai_resume_graduate  # or your project folder
uvicorn backend.app.main:app --reload
```

---

## Performance

### Q: How can I improve performance?

**A:**
- Use Docker for consistent environment
- Enable caching (Redis)
- Use PostgreSQL in production
- Run multiple backend instances
- Use GPU for embeddings
- Enable gzip compression in Nginx

### Q: What's the typical response time?

**A:**
- API: < 200ms
- CV parsing: 200-500ms
- Matching: 50-100ms per candidate
- Frontend: < 1 second load

---

## Security

### Q: Is HireMind secure?

**A:** Yes, it includes:
- JWT authentication
- Password hashing (bcrypt)
- Input validation
- CORS protection
- SQL injection prevention
- HTTPS support

### Q: How do I secure my `.env` file?

**A:**
```bash
# Never commit .env
git add .gitignore  # This ignores .env

# Use .env.example as template
cp .env.example .env

# For production, use:
# - Environment variables
# - Secret management (AWS Secrets, HashiCorp Vault)
# - CI/CD variables
```

### Q: Can I use HireMind with HTTPS?

**A:** Yes. In production, use Nginx with SSL or a CDN (Cloudflare). See [DEPLOYMENT.md](../DEPLOYMENT.md).

---

## Contributing

### Q: How do I report a bug?

**A:** Open an issue on GitHub:
1. Go to [Issues](https://github.com/yourusername/HireMind/issues)
2. Click "New Issue"
3. Use bug report template
4. Include details and reproduction steps

### Q: How do I contribute code?

**A:**
1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Make changes
4. Run tests: `make check`
5. Commit: `git commit -m "feat: my feature"`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

See [CONTRIBUTING.md](../CONTRIBUTING.md)

### Q: What's the code style?

**A:**
- Python: PEP 8 (Black formatter)
- JavaScript: Prettier formatter
- Use `make lint` to check

---

## Advanced

### Q: Can I use custom embedding models?

**A:** Yes! In `ai_engine/embeddings.py`, change the model name:
```python
model_name = "sentence-transformers/all-MiniLM-L6-v2"  # Change this
```

Available models: [Hugging Face Model Hub](https://huggingface.co/models?library=sentence-transformers)

### Q: How do I fine-tune the model?

**A:** Run training scripts:
```bash
cd ai_engine/training
python prepare_dataset.py
python train_sentence_model.py
python evaluate_model.py
```

See [README.md](../README.md) for detailed steps.

### Q: Can I integrate with external services?

**A:** Yes, the API is extensible. You can:
- Add new routes easily
- Integrate Slack, email notifications
- Connect to external job boards
- Add video interview support

---

## Getting Help

Still have questions?

- 📖 [Documentation](./index.md)
- 🐛 [Report Bug](https://github.com/yourusername/HireMind/issues)
- 💬 [Ask Question](https://github.com/yourusername/HireMind/discussions)
- 📧 [Email Support](mailto:support@hiremind.app)

---

**Last Updated:** April 2024
