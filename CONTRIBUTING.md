# Contributing to HireMind

Thank you for your interest in contributing to HireMind! We welcome contributions of all kinds.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots and animated GIFs if possible**
* **Include your environment details** (OS, Python version, Node version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and expected behavior**
* **Explain why this enhancement would be useful**

### Pull Requests

* Fill in the required PR template
* Follow the Python and JavaScript style guides
* Include appropriate test cases
* End all files with a newline
* Avoid platform-dependent code
* Document new code with comments and docstrings

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### Setup Steps

```bash
# Clone the repo
git clone https://github.com/yourusername/HireMind.git
cd HireMind

# Setup backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # or source .venv/bin/activate on macOS/Linux
pip install -r backend/requirements.txt

# Setup frontend
cd frontend
npm install
npm run build
cd ..

# Run backend
uvicorn backend.app.main:app --reload

# In another terminal, run frontend
cd frontend && npm run dev
```

## Style Guides

### Python Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Use type hints where possible
- Keep functions focused and modular

Example:
```python
def calculate_match_score(
    cv_embedding: np.ndarray, 
    job_embedding: np.ndarray
) -> float:
    """
    Calculate semantic similarity between CV and job.
    
    Args:
        cv_embedding: Embedding vector for CV
        job_embedding: Embedding vector for job
        
    Returns:
        Cosine similarity score (0-1)
    """
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity([cv_embedding], [job_embedding])[0][0]
```

### JavaScript/React Code Style
- Use ES6+ syntax
- Use meaningful component and variable names
- Keep components focused and reusable
- Use Tailwind CSS for styling (no inline styles)
- Add JSDoc comments for complex logic

Example:
```javascript
/**
 * Display candidate match score with visual indicator
 * @param {Object} props - Component props
 * @param {number} props.score - Match score (0-100)
 * @param {string} props.label - Label text
 * @returns {JSX.Element}
 */
function ScoreIndicator({ score, label }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium">{label}</span>
      <div className="bg-gray-200 rounded-full w-24 h-2">
        <div 
          className="bg-orange-500 h-full rounded-full transition-all"
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
```

## Testing

- Write tests for new features
- Tests should be in `backend/tests/` or `frontend/tests/`
- Run tests before submitting PR:
  ```bash
  # Backend
  pytest backend/tests/ -v
  
  # Frontend
  npm run test
  ```

## Commit Messages

Follow conventional commits format:

```
feat: add new match algorithm
fix: resolve CV parsing issue
docs: update installation guide
style: fix code formatting
test: add matching algorithm tests
chore: update dependencies
```

## Additional Notes

### Issue and Pull Request Labels

* `bug` - Something isn't working
* `enhancement` - New feature or request
* `documentation` - Improvements or additions to documentation
* `good first issue` - Good for newcomers
* `help wanted` - Extra attention is needed
* `question` - Further information is requested

### Project Structure
- Backend logic in `backend/app/`
- Frontend components in `frontend/src/`
- AI/ML code in `ai_engine/`
- Database schemas in `database/`

## Recognition

Contributors will be recognized in:
- README.md acknowledgments section
- Release notes
- GitHub contributors page

Thank you for contributing to HireMind! 🎉
