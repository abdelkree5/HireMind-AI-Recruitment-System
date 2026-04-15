# API Guide

## Overview

HireMind uses a RESTful API built with FastAPI. All responses are JSON, and all requests should include the `Content-Type: application/json` header.

**Base URL:** `http://localhost:8000` (development)

## Authentication

HireMind uses JWT (JSON Web Tokens) for authentication.

### Login
Get a token by logging in:

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "candidate"
  }
}
```

### Using the Token
Include the token in subsequent requests:

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Authentication Endpoints

### Register

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "role": "candidate",
  "name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "candidate",
  "name": "John Doe"
}
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "token...",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /api/auth/me
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "candidate",
  "name": "John Doe"
}
```

## CV Endpoints

### Upload CV

```http
POST /api/cv/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <binary-file>
```

**Response:** `201 Created`
```json
{
  "cv_id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "experience": "5 years",
  "skills": ["Python", "React", "FastAPI"],
  "education": ["BS Computer Science"],
  "analysis": {
    "skill_score": 85,
    "experience_level": "intermediate"
  }
}
```

### Get CV Analysis

```http
GET /api/cv/{cv_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "cv_id": "uuid",
  "profile": {...},
  "skills": [
    {"name": "Python", "level": "expert", "relevance": 0.95},
    {"name": "React", "level": "intermediate", "relevance": 0.87}
  ],
  "recommendations": ["Learn TypeScript", "Expand DevOps skills"]
}
```

### List CVs

```http
GET /api/cv/list
Authorization: Bearer {token}
```

**Response:**
```json
{
  "cvs": [
    {"cv_id": "uuid", "uploaded_at": "2024-01-15T10:30:00Z"},
    {"cv_id": "uuid2", "uploaded_at": "2024-01-10T14:20:00Z"}
  ]
}
```

### Delete CV

```http
DELETE /api/cv/{cv_id}
Authorization: Bearer {token}
```

**Response:** `204 No Content`

## Job Endpoints

### Create Job

```http
POST /api/jobs
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Senior Python Developer",
  "description": "Looking for an experienced Python developer...",
  "skills_required": ["Python", "FastAPI", "PostgreSQL"],
  "experience_level": "intermediate",
  "location": "Remote"
}
```

**Response:** `201 Created`
```json
{
  "job_id": "uuid",
  "title": "Senior Python Developer",
  "company_id": "uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "active"
}
```

### List Jobs

```http
GET /api/jobs?search=python&location=remote&skip=0&limit=10
Authorization: Bearer {token}
```

**Query Parameters:**
- `search` - Search in title and description
- `location` - Filter by location
- `skip` - Skip N results (pagination)
- `limit` - Limit results per page

**Response:**
```json
{
  "total": 45,
  "jobs": [
    {
      "job_id": "uuid",
      "title": "Senior Python Developer",
      "company": "TechCorp",
      "match_score": 85
    }
  ]
}
```

### Get Job Details

```http
GET /api/jobs/{job_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "job_id": "uuid",
  "title": "Senior Python Developer",
  "description": "...",
  "skills_required": ["Python", "FastAPI"],
  "company": {...},
  "applicants_count": 12
}
```

### Update Job

```http
PUT /api/jobs/{job_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Senior Python Developer (Updated)",
  "description": "...",
  "skills_required": ["Python", "FastAPI", "Docker"]
}
```

### Delete Job

```http
DELETE /api/jobs/{job_id}
Authorization: Bearer {token}
```

## Matching Endpoints

### Get Matched Candidates for Job

```http
POST /api/match/candidates
Authorization: Bearer {token}
Content-Type: application/json

{
  "job_id": "uuid",
  "limit": 10
}
```

**Response:**
```json
{
  "matches": [
    {
      "candidate_id": "uuid",
      "name": "Jane Doe",
      "match_score": 92,
      "skill_match": 0.95,
      "experience_fit": 0.90,
      "skills": ["Python", "FastAPI", "React"]
    }
  ]
}
```

### Get Matched Jobs for Candidate

```http
GET /api/match/jobs
Authorization: Bearer {token}
```

**Response:**
```json
{
  "matches": [
    {
      "job_id": "uuid",
      "title": "Senior Python Developer",
      "company": "TechCorp",
      "match_score": 87,
      "matching_skills": ["Python", "FastAPI"]
    }
  ]
}
```

## Interview Endpoints

### Start Interview

```http
POST /api/chat/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "job_id": "uuid",
  "candidate_id": "uuid"
}
```

**Response:**
```json
{
  "interview_id": "uuid",
  "initial_question": "Tell me about your Python experience..."
}
```

### Send Message

```http
POST /api/chat/send
Authorization: Bearer {token}
Content-Type: application/json

{
  "interview_id": "uuid",
  "message": "I have 5 years of Python experience..."
}
```

**Response:**
```json
{
  "response": "That's great! Can you tell me more about...",
  "score_update": {
    "technical": 85,
    "communication": 78,
    "experience": 88
  }
}
```

### Get Interview History

```http
GET /api/chat/{interview_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "interview_id": "uuid",
  "messages": [
    {"role": "ai", "content": "..."},
    {"role": "candidate", "content": "..."}
  ],
  "current_scores": {...}
}
```

### Get Interview Score

```http
GET /api/chat/{interview_id}/score
Authorization: Bearer {token}
```

**Response:**
```json
{
  "technical_score": 85,
  "communication_score": 78,
  "experience_score": 88,
  "final_score": 83,
  "feedback": "Strong technical knowledge..."
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- **Unauthenticated:** 10 requests/minute
- **Authenticated:** 100 requests/minute
- **Upload:** 5 files/minute

## Pagination

For list endpoints:

```http
GET /api/jobs?skip=0&limit=10&sort_by=created_at&order=desc
```

**Response includes:**
```json
{
  "total": 150,
  "skip": 0,
  "limit": 10,
  "items": [...]
}
```

## WebSocket Endpoints

Real-time updates (coming in v1.1):

```
ws://localhost:8000/ws/{user_id}
```

## API Documentation

**Interactive Docs:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

---

**Last Updated:** April 2024
