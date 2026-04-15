# HireMind Documentation

> Comprehensive documentation site for HireMind AI Recruitment Platform

## 📚 Documentation Structure

- **[Getting Started](./getting-started.md)** - Quick setup and first steps
- **[Architecture](./architecture.md)** - System design and components
- **[API Guide](./api-guide.md)** - REST API documentation
- **[Development](./development.md)** - Development workflow and tools
- **[Deployment](./deployment.md)** - Production deployment guide
- **[Contributing](./contributing.md)** - How to contribute
- **[FAQ](./faq.md)** - Frequently asked questions

## 🎯 Quick Links

### For Users
- [Installation Guide](#installation)
- [How it Works](#how-it-works)
- [Features Overview](#features)

### For Developers
- [Project Structure](#structure)
- [Development Setup](#development)
- [API Documentation](#api)

### For Contributors
- [Contributing Guide](./contributing.md)
- [Code of Conduct](#conduct)
- [Bug Reports & Features](#issues)

---

## 🚀 Installation

**Option 1: Docker (Recommended)**
```bash
docker-compose up
```

**Option 2: Local Setup**
```bash
# Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

---

## 📖 Documentation Files

Visit the `/docs` folder in the repository for detailed documentation on:

- **Setup & Installation** - Getting HireMind running
- **Architecture** - How the system is designed
- **API Reference** - Complete API documentation
- **Deployment Guide** - Production setup
- **Development Guide** - Contributing to HireMind
- **Configuration** - Customizing HireMind
- **Troubleshooting** - Common issues and solutions

---

## 🔗 External Resources

- [GitHub Repository](https://github.com/yourusername/HireMind)
- [Issue Tracker](https://github.com/yourusername/HireMind/issues)
- [Discussions](https://github.com/yourusername/HireMind/discussions)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

---

## 📧 Support

- 📖 Documentation: This site
- 🐛 Report bugs: [GitHub Issues](https://github.com/yourusername/HireMind/issues)
- 💬 Ask questions: [GitHub Discussions](https://github.com/yourusername/HireMind/discussions)
- 📧 Email: support@hiremind.app

---

**Last Updated:** April 2024
