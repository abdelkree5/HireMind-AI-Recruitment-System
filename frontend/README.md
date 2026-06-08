# Frontend - HireMind Platform

## Overview

This is the React 18 + Tailwind CSS frontend for the HireMind AI-powered recruitment platform. It provides interfaces for:

- **Candidates**: CV upload, job search, applications, interviews
- **Companies**: Job posting, candidate management, ranking

## Technology Stack

- **Framework**: React 18.3.1
- **Router**: React Router 7.14.1
- **Styling**: Tailwind CSS 3.4.17 with PostCSS
- **Build Tool**: Vite 6.4.2
- **Language**: JavaScript/JSX

## Project Structure

```
frontend/
├── src/
│   ├── pages/                      # Page components
│   │   ├── AuthPage.jsx
│   │   ├── RoleSelectionPage.jsx
│   │   ├── CandidateDashboardPage.jsx
│   │   ├── CompanyDashboardPage.jsx
│   │   └── ...
│   ├── components/                 # Reusable components
│   │   ├── SaaSPrimitives.jsx
│   │   ├── AppLayout.jsx
│   │   ├── AppSidebar.jsx
│   │   ├── InterviewChat.jsx
│   │   └── ...
│   ├── layout/                     # Layout components
│   │   └── AppLayout.jsx
│   ├── api/                        # API client
│   │   └── client.js
│   ├── App.jsx                     # Root component with routing
│   ├── main.jsx                    # Entry point
│   └── index.css                   # Tailwind + custom styles
├── public/                         # Static assets
├── dist/                          # Production build (git-ignored)
├── index.html                     # HTML entry point
├── package.json                   # Dependencies & scripts
├── vite.config.js                # Vite configuration
├── tailwind.config.js            # Tailwind theme
├── postcss.config.js             # PostCSS plugins
└── README.md                      # This file
```

## Installation

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Setup

```bash
# Copy environment file
cp ../.env.example .env.local

# Edit .env.local with your API endpoint
# VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Development

### Running Dev Server

```bash
npm run dev
```

Server runs at: **http://localhost:5173**

Features:

- Hot module replacement (HMR)
- Fast refresh on file changes
- Tailwind CSS compilation in real-time

### Building for Production

```bash
npm run build
```

Output:

- Compiled files in `dist/`
- CSS: ~19.6 KB (gzipped ~4.6 KB)
- JS: ~236 KB (gzipped ~72 KB)

### Preview Production Build

```bash
npm run preview
```

Serves the production build locally for testing.

## Key Features

### Authentication

- User registration with role selection (Candidate/Company)
- Login with JWT tokens
- Demo credentials for testing
- Protected routes with role-based access

### Candidate Portal

1. **Dashboard**
   - Match score summary
   - AI evaluation results
   - Recommended jobs count
   - Recent activity timeline

2. **CV Analysis**
   - Drag-drop file upload
   - Supports: PDF, DOCX, TXT
   - Displays parsed profile
   - Shows extracted skills
   - Highlights strengths & weaknesses

3. **Job Search**
   - Browsable job listings
   - Search and filter
   - Inline application form
   - Match scores displayed

4. **Matching**
   - View matched jobs
   - See matching breakdown
   - Skill recommendations

5. **AI Interview**
   - Real-time chat interface
   - Live scoring display
   - Interview history

6. **Applications**
   - Track submitted applications
   - View status (pending/approved/rejected)
   - Application history

### Company Portal

1. **Dashboard**
   - Total jobs, applicants, top candidates
   - Recent applicants table
   - Quick stats

2. **Add Job**
   - Post new position
   - Specify requirements
   - Skill requirements editor

3. **Manage Jobs**
   - Edit job postings
   - Delete jobs
   - View applicants per job

4. **Applicants**
   - View all candidates
   - Match scores displayed
   - AI evaluation scores
   - View CV action

5. **Ranking**
   - Ranked candidate list
   - Sorted by match score
   - Color-coded scores
   - Export ready

## Styling

### Tailwind CSS Setup

Configuration:

- **File**: `tailwind.config.js`
- **Custom Colors**: Brand colors (orange/white theme)
- **Utilities**: Shadow, border-radius customizations

### Custom Styles

Located in `src/index.css`:

- Tailwind directives (`@tailwind`)
- Custom utilities (`.glass`)
- Font imports (Manrope)
- Keyframe animations (`@keyframes floatPulse`)

### Component Library

**SaaSPrimitives.jsx** - Reusable components:

- `Panel` - Card wrapper
- `StatCard` - KPI display
- `Badge` - Tag/label
- `EmptyState` - No data display
- `Modal` - Dialog component
- `Toast` - Notification
- `InlineLoader` - Loading indicator

## API Integration

### Client Setup

File: `src/api/client.js`

Features:

- Centralized HTTP client
- Token-based authentication
- Error handling
- Form data support for uploads

### Endpoints Used

| Method | Endpoint                | Purpose                |
| ------ | ----------------------- | ---------------------- |
| POST   | `/api/auth/register`    | User registration      |
| POST   | `/api/auth/login`       | User login             |
| GET    | `/api/auth/me`          | Get current user       |
| POST   | `/api/cv/upload`        | Upload CV              |
| GET    | `/api/cv/{id}`          | Get CV details         |
| POST   | `/api/jobs`             | Create job             |
| GET    | `/api/jobs`             | List jobs              |
| POST   | `/api/match/candidates` | Get matched candidates |
| POST   | `/api/chat/send`        | Interview message      |

## State Management

### App-level State

Managed in `App.jsx`:

- User authentication state
- Current user role
- Application data (jobs, candidates)
- UI state (modals, loading)

Example:

```javascript
const [currentUser, setCurrentUser] = useState(null);
const [jobs, setJobs] = useState([]);
const [loading, setLoading] = useState(false);
```

## Routing

### Route Structure

```
/                          - Role selection page
/auth                      - Login/Register page
/company/*                 - Company portal routes
  /dashboard               - Company dashboard
  /add-job                 - Create job
  /jobs                    - Manage jobs
  /applicants              - View applicants
  /reports                 - Ranking/reports
  /settings                - Settings

/candidate/*              - Candidate portal routes
  /dashboard               - Candidate dashboard
  /analysis                - CV analysis
  /jobs                    - Job search
  /matching                - Job matching
  /interview               - AI interview
  /applications            - Track applications
  /settings                - Settings
```

Protection:

- PortalGuard wrapper on all protected routes
- Redirects to login if not authenticated
- Checks role authorization

## Performance

- Build time: < 30 seconds
- Page load: < 1 second
- CSS-in-JS optimized
- Code splitting enabled
- Image optimization ready

### Optimization Tips

- Use React.memo for expensive components
- Lazy load pages with React.lazy()
- Minimize bundle size
- Use production build for deployment

## Common Tasks

### Adding a New Page

1. Create file in `src/pages/MyPage.jsx`:

```javascript
export default function MyPage() {
  return <div>Page content</div>;
}
```

2. Add route in `App.jsx`:

```javascript
<Route path='/my-page' element={<MyPage />} />
```

### Creating a Component

1. File: `src/components/MyComponent.jsx`
2. Use Tailwind classes for styling
3. Export as default

### Updating Tailwind Theme

Edit `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    colors: {
      brand: '#FF7A00',
      // ...
    },
  },
};
```

Then run: `npm run build`

## Troubleshooting

### Issue: Port 5173 in use

**Solution**:

```bash
npm run dev -- --port 3000
```

### Issue: API not responding (CORS error)

**Solution**: Check `.env.local`:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

And verify backend is running:

```bash
# In backend terminal
uvicorn backend.app.main:app --reload
```

### Issue: Tailwind styles not applying

**Solution**: Rebuild CSS and restart dev server:

```bash
npm run build:css
npm run dev
```

### Issue: Module not found error

**Solution**: Clear node_modules and reinstall:

```bash
rm -r node_modules package-lock.json
npm install
npm run dev
```

## Testing

```bash
# Run tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

## Building for Production

### Steps

1. **Build**:

```bash
npm run build
```

2. **Test build**:

```bash
npm run preview
```

3. **Deploy**:

```bash
# Upload dist/ folder to hosting
# Examples: Vercel, Netlify, GitHub Pages, AWS S3
```

### Environment Variables for Production

Create `.env.production`:

```
VITE_API_BASE_URL=https://api.hiremind.app
VITE_APP_NAME=HireMind
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: Modern versions

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](../LICENSE) for details.

## Support

- 📧 Email: support@hiremind.app
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/HireMind/issues)
- 📖 Main README: [Project README](../README.md)

---

**Last Updated**: April 2024
