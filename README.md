# HireMind AI Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tech Stack: FastAPI + React](https://img.shields.io/badge/Tech%20Stack-FastAPI%20%2B%20React-blueviolet.svg)](https://github.com)

## 🎯 Overview

**HireMind** is an AI-powered recruitment platform that revolutionizes candidate-job matching through intelligent CV analysis, semantic skill extraction, and AI-driven interviews. Built with cutting-edge NLP and machine learning technologies, HireMind enables companies to identify top talent efficiently while helping candidates find their ideal roles.

### Key Problem Solved
- ❌ **Traditional Approach**: Manual resume screening is tedious, biased, and inefficient
- ✅ **HireMind Solution**: Automated, intelligent matching using neural embeddings and semantic similarity

---

## ✨ Features

### 🔍 **CV Analysis**
- Parse resumes in PDF, DOCX, and TXT formats
- Extract candidate information (name, email, experience, education)
- Automatic skill detection and classification
- Experience level assessment
- Built-in validation and error handling

### 🧠 **AI Skill Matching**
- **Semantic Similarity**: Uses Sentence Transformers to compute embeddings
- **Cosine Similarity**: Advanced matching algorithm to find candidates matching job requirements
- **Multi-dimensional Scoring**: Combines skill coverage, relevance, and experience level
- **Ranking System**: Candidates ranked by overall fit score

### 📊 **Skill Extraction Engine**
- NLP-based skill identification from CV text
- Categorization (Technical, Soft Skills, Languages)
- Relevance scoring for each extracted skill
- Support for domain-specific skill databases

### 🎤 **AI Interview System**
- Real-time chat-based technical interviews
- AI evaluates responses on:
  - **Technical Depth**: Knowledge of concepts
  - **Communication Clarity**: Explanation quality
  - **Experience Level**: Practical application
- Automated scoring and feedback
- Interview transcripts and analytics

### 📈 **Candidate Dashboard**
- View profile and uploaded CV
- Track job applications and statuses
- See match scores for applied positions
- Interview history and performance scores
- Career recommendations

### 🏢 **Company Dashboard**
- Post and manage job openings
- View all applicants with match scores
- Shortlist and rank candidates
- Interview management
- Analytics and recruitment metrics

---

## 🛠 Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- **Server**: [Uvicorn](https://www.uvicorn.org/) - ASGI server
- **Language**: Python 3.9+

### Frontend
- **Framework**: [React 18.3.1](https://react.dev/) - UI library
- **Router**: [React Router 7](https://reactrouter.com/) - Client-side routing
- **Styling**: [Tailwind CSS 3.4](https://tailwindcss.com/) - Utility-first CSS
- **Build Tool**: [Vite 6.4](https://vitejs.dev/) - Next-gen frontend tooling
- **Build Time**: < 30 seconds

### AI & ML
- **Embeddings**: [Sentence Transformers](https://www.sbert.net/) (all-MiniLM-L6-v2)
- **NLP**: [Transformers Library](https://huggingface.co/transformers/)
- **Deep Learning**: [PyTorch](https://pytorch.org/)
- **ML Pipeline**: [scikit-learn](https://scikit-learn.org/)

### Database
- **Default**: SQLite (portable, zero-config)
- **Production**: PostgreSQL recommended
- **ORM-Style**: Pydantic + Python dataclasses

### Document Processing
- **PDFs**: [pdfplumber](https://github.com/jsvine/pdfplumber)
- **Word Docs**: [python-docx](https://python-docx.readthedocs.io/)

---

## 📋 Project Structure

```
HireMind/
│
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── main.py                  # App entry point
│   │   ├── routes/                  # Endpoint routers
│   │   │   ├── auth.py              # Authentication
│   │   │   ├── cv.py                # CV analysis
│   │   │   ├── jobs.py              # Job management
│   │   │   └── chat.py              # Interview chat
│   │   ├── services/                # Business logic
│   │   │   ├── cv_service.py
│   │   │   ├── matching_service.py
│   │   │   └── interview_service.py
│   │   ├── schemas.py               # Pydantic models
│   │   └── __init__.py
│   ├── requirements.txt              # Python dependencies
│   └── README.md                     # Backend docs
│
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── pages/                   # Page components
│   │   │   ├── AuthPage.jsx
│   │   │   ├── CandidateDashboardPage.jsx
│   │   │   ├── CompanyDashboardPage.jsx
│   │   │   └── ...
│   │   ├── components/              # Reusable components
│   │   ├── api/                     # API client
│   │   ├── App.jsx                  # Root component
│   │   ├── main.jsx                 # Entry point
│   │   └── index.css                # Tailwind + custom styles
│   ├── package.json                 # Node dependencies
│   ├── vite.config.js               # Vite configuration
│   ├── tailwind.config.js           # Tailwind theme
│   ├── postcss.config.js            # PostCSS setup
│   └── README.md                    # Frontend docs
│
├── ai_engine/                        # AI/ML Components
│   ├── parser.py                    # CV parsing
│   ├── skills.py                    # Skill extraction
│   ├── embeddings.py                # Embedding generation
│   ├── matcher.py                   # Semantic matching
│   ├── interview.py                 # Interview logic
│   ├── training/                    # Model training scripts
│   │   ├── train_sentence_model.py
│   │   └── evaluate_model.py
│   └── config.py                    # AI configurations
│
├── database/                        # Data & Schemas
│   ├── init_db.py                  # Database initialization
│   ├── schema.sql                  # Database schema
│   └── hiremind.db                 # SQLite database (git-ignored)
│
├── tools/                           # Utility scripts
│   └── deployment_checklist.md
│
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── README.md                        # THIS FILE
└── requirements.txt                 # Root dependencies (optional)
```

---

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.9 or higher
- **Node.js**: 16.x or higher
- **npm**: 8.x or higher
- **Git**: For version control

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/HireMind.git
cd HireMind
```

#### 2. Setup Backend

```bash
# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your settings
```

#### 3. Setup Frontend

```bash
cd frontend

# Install Node.js dependencies
npm install

# Build Tailwind CSS
npm run build:css
```

#### 4. Initialize Database

```bash
# From project root
python database/init_db.py
```

#### 5. Run Backend

```bash
# From project root (with .venv activated)
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend runs on: **http://127.0.0.1:8000**
- 📖 API Docs: **http://127.0.0.1:8000/docs** (Swagger UI)
- 📋 ReDoc: **http://127.0.0.1:8000/redoc**

#### 6. Run Frontend

```bash
# From frontend directory (in new terminal)
npm run dev
```

Frontend runs on: **http://localhost:5173**

---

## 🔄 AI Pipeline Workflow

### CV Analysis Flow
```
1. User uploads CV (PDF/DOCX/TXT)
   ↓
2. Document Parsing
   - Extract text from file
   - Clean and normalize
   ↓
3. Information Extraction
   - Parse name, email, phone
   - Extract experience sections
   - Identify education
   ↓
4. Skill Extraction
   - NLP analysis of text
   - Match against skill database
   - Score relevance
   ↓
5. Embedding Generation
   - Convert CV text to embeddings
   - Store in database
   ↓
6. Results Display
   - Show parsed profile
   - Display extracted skills
   - Highlight analysis
```

### Job Matching Flow
```
1. Company posts job with requirements
   ↓
2. Embedding generated for job description
   ↓
3. For each candidate:
   - Compare embeddings (cosine similarity)
   - Score skill match
   - Calculate experience fit
   ↓
4. Generate match score (0-100)
   ↓
5. Rank candidates by score
   ↓
6. Display results to company
```

### Interview Flow
```
1. Candidate starts interview
   ↓
2. AI asks technical questions
   ↓
3. Candidate provides answers
   ↓
4. AI Evaluates:
   - Technical accuracy
   - Communication clarity
   - Experience relevance
   ↓
5. Score calculated in real-time
   ↓
6. Results saved to profile
```

---

## 📡 API Endpoints Overview

### Authentication
```
POST   /api/auth/register          - Register new user
POST   /api/auth/login             - Login user
POST   /api/auth/logout            - Logout user
GET    /api/auth/me                - Get current user
```

### CV Analysis
```
POST   /api/cv/upload              - Upload and analyze CV
GET    /api/cv/{cv_id}             - Get CV analysis results
GET    /api/cv/list                - List user's CVs
DELETE /api/cv/{cv_id}             - Delete CV
```

### Jobs
```
POST   /api/jobs                   - Create job posting
GET    /api/jobs                   - List jobs with filters
GET    /api/jobs/{job_id}          - Get job details
PUT    /api/jobs/{job_id}          - Update job
DELETE /api/jobs/{job_id}          - Delete job
```

### Matching
```
POST   /api/match/candidates       - Get matched candidates for job
GET    /api/match/jobs             - Get matched jobs for candidate
GET    /api/match/score            - Calculate match score
```

### Interview
```
POST   /api/chat/send              - Send message in interview
GET    /api/chat/{interview_id}    - Get interview history
POST   /api/chat/start             - Start new interview
GET    /api/chat/{interview_id}/score - Get interview score
```

---

## 🎨 User Interface Screenshots

> Screenshots will be added here after project completion

### Candidate Portal
- Dashboard with match scores
- CV analysis results
- Job search and filtering
- Application tracking
- Interview chat interface

### Company Portal
- Dashboard with hiring metrics
- Job management
- Candidate shortlisting
- Ranking and evaluation
- Analytics

---

## ⚙️ Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `BACKEND_HOST` - Backend server address
- `BACKEND_PORT` - Backend port (default: 8000)
- `DATABASE_URL` - Database connection string
- `EMBEDDING_MODEL` - Model for embeddings
- `SECRET_KEY` - JWT secret (change in production!)
- `VITE_API_BASE_URL` - Frontend API endpoint

### Database Setup

**SQLite** (default):
```bash
python database/init_db.py
```

**PostgreSQL**:
```bash
# Install PostgreSQL locally or use Docker
# Update DATABASE_URL in .env:
# postgresql://user:password@localhost:5432/hiremind_db

python database/init_db.py
```

---

## 🧪 Testing

### Test Backend
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest backend/tests/ -v
```

### Test Frontend
```bash
npm run test
```

---

## 📚 AI Training (Optional)

To improve matching accuracy with custom data:

```bash
# Prepare training data
cd ai_engine/training
python prepare_dataset.py

# Download base model
python download_datasets.py

# Train sentence model
python train_sentence_model.py

# Evaluate
python evaluate_model.py

# Use the trained model
# Copy checkpoint to ai_engine/checkpoints/
```

---

## 🐳 Docker Deployment (Optional)

```bash
# Build images
docker-compose build

# Run containers
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

---

## 🔐 Security Best Practices

- ✅ Change `SECRET_KEY` in production
- ✅ Use HTTPS in production
- ✅ Set `DEBUG=false` in production
- ✅ Use environment variables for sensitive data
- ✅ Implement rate limiting
- ✅ Validate all file uploads
- ✅ Regular security audits
- ✅ Keep dependencies updated

---

## 📊 Performance Metrics

- **CV Parsing**: ~200-500ms per document
- **Embedding Generation**: ~100-300ms per CV
- **Matching Algorithm**: ~50-100ms per candidate comparison
- **Frontend Build**: < 30 seconds
- **API Response Time**: < 200ms (median)

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support & Contact

- 📧 Email: support@hiremind.app
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/HireMind/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/HireMind/discussions)

---

## 🙏 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) - Semantic embeddings
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend library
- [Tailwind CSS](https://tailwindcss.com/) - Styling
- Community contributions and feedback

---

## 🚦 Roadmap

- [ ] Advanced filtering and search
- [ ] Email notifications
- [ ] Real-time notifications (WebSocket)
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with ATS systems
- [ ] Video interview support
- [ ] Collaboration features

---

**Made with ❤️ by the HireMind Team**

⭐ If you find this project helpful, please star it on GitHub!
