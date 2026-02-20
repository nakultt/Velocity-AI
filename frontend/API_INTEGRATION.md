# API Integration Guide

Complete guide for integrating this frontend template with your backend.

---

## Table of Contents
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Authentication Flow](#authentication-flow)
- [API Endpoints](#api-endpoints)
- [Request/Response Examples](#requestresponse-examples)
- [TypeScript Interfaces](#typescript-interfaces)
- [Error Handling](#error-handling)
- [Testing](#testing)

---

## Quick Start

### 1. Configure Backend URL

**Option A: Environment Variable (Recommended)**
Create `.env` file in project root:
```env
VITE_API_URL=https://api.yourapp.com
```

**Option B: Config File**
Edit `src/config/app.config.ts`:
```typescript
api: {
  baseUrl: 'https://api.yourapp.com'
}
```

### 2. Set Up CORS on Backend
Allow requests from your frontend domain:
```python
# FastAPI Example
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Configuration

### App Settings (`src/config/app.config.ts`)

```typescript
export const APP_CONFIG = {
  name: 'YourAppName',           // Your app name
  logo: '/logo.png',              // Logo path (in /public folder)
  version: '1.0.0',
  copyright: '© 2024 YourAppName. All rights reserved.',
  
  storageKeys: {
    user: 'yourapp_user',         // localStorage key for user data
    remember: 'yourapp_remember'   // localStorage key for remember me
  },
  
  api: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000'
  },
  
  dev: {
    bypassLogin: false  // Set true to skip authentication (dev only!)
  }
};
```

---

## Authentication Flow

### How It Works

1. **Login**: User enters credentials → Backend returns `User` object with `token`
2. **Storage**: Token stored in `localStorage` (if "remember me") or `sessionStorage`
3. **Requests**: Token sent in `Authorization: Bearer <token>` header
4. **Logout**: Token removed from storage

### Token Storage

```typescript
// Stored as JSON string
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Storage Key**: `{APP_NAME}_user` (e.g., `myapp_user`)

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

All requests include:
```
Content-Type: application/json
```

Protected endpoints include:
```
Authorization: Bearer {token}
```

---

## Request/Response Examples

### 1. Authentication

#### **POST /auth/signup**
Create a new user account.

**Request:**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123",
    "name": "John Doe"
  }'
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepass123",
  "name": "John Doe"  // optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "john@example.com",
  "name": "John Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0...",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Email already exists"
}
```

---

#### **POST /auth/login**
Authenticate existing user.

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123",
    "remember_me": true
  }'
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepass123",
  "remember_me": true  // optional, default false
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "john@example.com",
  "name": "John Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid credentials"
}
```

---

#### **PUT /auth/user/{userId}**
Update user profile.

**Request:**
```bash
curl -X PUT http://localhost:8000/auth/user/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGci..." \
  -d '{
    "name": "John Smith",
    "email": "johnsmith@example.com",
    "password": "newpassword123"
  }'
```

**Request Body:**
```json
{
  "name": "John Smith",      // optional
  "email": "new@email.com",  // optional
  "password": "newpass123"   // optional
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "johnsmith@example.com",
  "name": "John Smith",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### 2. Chat

#### **POST /api/chat**
Send a chat message.

**Request:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGci..." \
  -d '{
    "user_id": 1,
    "message": "Schedule a meeting for tomorrow at 3pm",
    "smart_mode": false,
    "conversation_id": 123
  }'
```

**Request Body:**
```json
{
  "user_id": 1,
  "message": "Schedule a meeting for tomorrow at 3pm",
  "smart_mode": false,  // optional, default false
  "conversation_id": 123  // optional, creates new if not provided
}
```

**Response (200 OK):**
```json
{
  "message": "I've scheduled a meeting for tomorrow at 3pm.",
  "conversation_id": 123,
  "raw_response": "Full AI response text..."
}
```

---

### 3. Conversations

#### **POST /api/conversations**
Create a new conversation.

**Request:**
```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGci..." \
  -d '{
    "user_id": 1,
    "title": "Project Planning"
  }'
```

**Request Body:**
```json
{
  "user_id": 1,
  "title": "Project Planning"  // optional, auto-generated if not provided
}
```

**Response (200 OK):**
```json
{
  "id": 123,
  "title": "Project Planning",
  "owner_id": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

---

#### **GET /api/conversations/{userId}**
Get all conversations for a user.

**Request:**
```bash
curl -X GET http://localhost:8000/api/conversations/1 \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response (200 OK):**
```json
{
  "conversations": [
    {
      "id": 123,
      "title": "Project Planning",
      "owner_id": 1,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:30:00Z"
    },
    {
      "id": 124,
      "title": "Daily Standup Notes",
      "owner_id": 1,
      "created_at": "2024-01-02T09:00:00Z",
      "updated_at": "2024-01-02T09:15:00Z"
    }
  ],
  "total": 2
}
```

---

#### **GET /api/conversations/{conversationId}/messages**
Get all messages in a conversation.

**Request:**
```bash
curl -X GET http://localhost:8000/api/conversations/123/messages \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "conversation_id": 123,
    "role": "user",
    "content": "Hello, can you help me?",
    "created_at": "2024-01-01T12:00:00Z"
  },
  {
    "id": 2,
    "conversation_id": 123,
    "role": "assistant",
    "content": "Of course! What do you need help with?",
    "created_at": "2024-01-01T12:00:05Z"
  },
  {
    "id": 3,
    "conversation_id": 123,
    "role": "user",
    "content": "Create a task for the new feature",
    "created_at": "2024-01-01T12:01:00Z"
  },
  {
    "id": 4,
    "conversation_id": 123,
    "role": "assistant",
    "content": "I've created a task for the new feature.",
    "created_at": "2024-01-01T12:01:10Z"
  }
]
```

---

#### **PUT /api/conversations/{conversationId}**
Update conversation title.

**Request:**
```bash
curl -X PUT http://localhost:8000/api/conversations/123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGci..." \
  -d '{
    "title": "Updated Title"
  }'
```

**Request Body:**
```json
{
  "title": "Updated Title"
}
```

**Response (200 OK):**
```json
{
  "id": 123,
  "title": "Updated Title",
  "owner_id": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z"
}
```

---

#### **DELETE /api/conversations/{conversationId}**
Delete a conversation and all its messages.

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/conversations/123 \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response (204 No Content)**
No response body.

---

### 4. Health Check

#### **GET /health**
Check if API is running.

**Request:**
```bash
curl -X GET http://localhost:8000/health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "YourAppName"
}
```

---

## TypeScript Interfaces

These are defined in `src/lib/api.ts`. Use them for type safety in your backend.

### User
```typescript
interface User {
  id: number;
  email: string;
  name?: string;
  token?: string;
  created_at?: string;
}
```

### Chat Response
```typescript
interface ChatResponse {
  message: string;
  raw_response?: string;
  conversation_id?: number;
}
```

### Conversation
```typescript
interface Conversation {
  id: number;
  title: string;
  owner_id: number;
  created_at: string;
  updated_at?: string;
}

interface ConversationList {
  conversations: Conversation[];
  total: number;
}
```

### Message
```typescript
interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
```
  type: "planning" | "plan" | "task_started" | "task_completed" | 
        "task_failed" | "complete" | "error";
  data: any;
}
```

---

## Error Handling

### Standard Error Response
All errors return this format:

```json
{
  "detail": "Error message here",
  "error_code": "OPTIONAL_ERROR_CODE"
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Valid token but no permission |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Backend error |

### Frontend Error Handling

The frontend catches and displays errors automatically. Backend should return:

```json
{
  "detail": "User-friendly error message"
}
```

Example error responses:

**400 Bad Request:**
```json
{
  "detail": "Password must be at least 8 characters"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

**404 Not Found:**
```json
{
  "detail": "Conversation not found"
}
```

---

## Testing

### Using curl

Test authentication:
```bash
# Signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

Test chat (replace TOKEN):
```bash
TOKEN="your_token_here"

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": 1,
    "message": "Hello, world!"
  }'
```

Test SSE streaming:
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
### Using cURL

Test basic chat:
```bash
# Login first
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  | jq -r '.token')

# Send chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "message": "Test message"
  }'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "test@example.com",
    "password": "test123"
})
user_data = response.json()
token = user_data["token"]

# Chat
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{BASE_URL}/api/chat", 
    headers=headers,
    json={
        "user_id": user_data["id"],
        "message": "Hello!"
    }
)
print(response.json())
```

---

## Backend Implementation Examples

### FastAPI Example

```python
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio

app = FastAPI()

# Models
class SignupRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    token: str
    created_at: str

# Auth dependency
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, detail="Missing or invalid token")
    token = authorization.replace("Bearer ", "")
    # Verify token and return user
    # ... your token verification logic
    return user

# Endpoints
@app.post("/auth/signup", response_model=UserResponse)
async def signup(data: SignupRequest):
    # Your signup logic
    return {
        "id": 1,
        "email": data.email,
        "name": data.name,
        "token": "generated_jwt_token",
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.post("/auth/login", response_model=UserResponse)
async def login(data: LoginRequest):
    # Your login logic
    return {
        "id": 1,
        "email": data.email,
        "name": "User Name",
        "token": "generated_jwt_token",
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.post("/api/chat")
async def chat(
    request: dict,
    user = Depends(get_current_user)
):
    # Your chat logic - process the message and return response
    return {
        "message": "AI response here",
        "conversation_id": request.get("conversation_id", 1),
        "raw_response": "Full response..."
    }
```

### Express.js Example

```javascript
const express = require('express');
const app = express();

app.use(express.json());

// Auth middleware
const authenticate = (req, res, next) => {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return res.status(401).json({ detail: 'Missing or invalid token' });
  }
  const token = auth.replace('Bearer ', '');
  // Verify token
  req.user = { id: 1 }; // Your user from token
  next();
};

// Signup
app.post('/auth/signup', async (req, res) => {
  const { email, password, name } = req.body;
  // Your signup logic
  res.json({
    id: 1,
    email,
    name,
    token: 'generated_jwt_token',
    created_at: new Date().toISOString()
  });
});

// Chat
app.post('/api/chat', authenticate, async (req, res) => {
  const { message, conversation_id, smart_mode } = req.body;
  
  // Your chat logic
  res.json({
    message: 'AI response here',
    conversation_id: conversation_id || 1,
    raw_response: 'Full response...'
  });
});
```

---

## Summary

### Required Endpoints (Minimum)
1. `POST /auth/login` - User authentication
2. `POST /api/chat` - Chat endpoint
3. `GET /api/conversations/{userId}` - List conversations
4. `GET /api/conversations/{conversationId}/messages` - Load chat history

### Optional Endpoints
- `POST /auth/signup` - User registration (can disable in frontend)
- `PUT /auth/user/{userId}` - Update profile (can disable in settings)
- `POST /api/conversations` - Create conversation (frontend auto-creates)
- `DELETE /api/conversations/{conversationId}` - Delete conversation

### Key Requirements
✅ Return proper HTTP status codes
✅ Use JWT tokens in `Authorization: Bearer {token}` header
✅ Return errors as `{"detail": "message"}`
✅ Support CORS for your frontend domain

---

## Need Help?

Check these files in the frontend:
- `src/lib/api.ts` - All API functions and types
- `src/config/app.config.ts` - Configuration
- `src/context/AuthContext.tsx` - Authentication logic
- `src/components/chat/chat-box.tsx` - Chat implementation
