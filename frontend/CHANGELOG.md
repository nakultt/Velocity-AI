# Changelog

## v2.0.0 - Template Simplification

### ✅ Removed Features (Project-Specific)

#### 1. **SSE Streaming**
- Removed `streamChatMessage()` function from `src/lib/api.ts`
- Removed `StreamEvent` interface and related types
- Removed streaming UI components from `chat-box.tsx`:
  - Live task cards
  - Real-time status indicators
  - Task progress displays
- Updated to simple request/response pattern with `sendChatMessage()`

#### 2. **Actions/Integrations Tracking**
- Removed `ActionResult` interface
- Removed `actions_taken` field from:
  - `ChatResponse` interface
  - `Message` interface
  - Message loading logic
  - Chat UI rendering
- No longer displays tool/service execution results

#### 3. **Supported Commands Endpoint**
- Removed `getSupportedCommands()` function from API client
- Removed endpoint documentation

#### 4. **Gemini API Integration**
- Removed Gemini-specific API functions:
  - `getGeminiApiKey()`
  - `updateGeminiApiKey()`
- Removed Gemini settings section from settings page
- Removed API key modal from chat interface

### ✨ Kept Features (Core Template)

#### **Authentication**
- JWT token-based authentication
- Login/Signup pages
- User profile management
- Remember me functionality
- Bypass login toggle (development mode)

#### **Chat Interface**
- Clean message display (user & AI bubbles)
- Basic request/response chat
- Smart mode toggle
- Animated placeholders
- Loading indicators (dots animation)

#### **Conversation Management**
- Create conversations
- List user conversations
- Load conversation history
- Update conversation titles
- Delete conversations
- Automatic conversation creation

#### **Configuration System**
- Centralized `APP_CONFIG` in `src/config/app.config.ts`
- Template placeholders (`{{APP_NAME}}`, `{{APP_LOGO}}`)
- Environment variable support
- Storage key customization

### 📝 Documentation Updates

#### **Updated Files**
1. **API_INTEGRATION.md**
   - Removed SSE streaming documentation
   - Removed action/integration tracking docs
   - Removed supported-commands endpoint
   - Simplified chat endpoint to basic POST request
   - Updated TypeScript interfaces
   - Removed TaskUpdate and StreamEvent types
   - Updated backend examples (FastAPI, Express.js)

2. **src/lib/api.ts**
   - Simplified `ChatResponse` interface
   - Simplified `Message` interface (removed actions_taken)
   - Kept all conversation management functions
   - Kept authentication functions

3. **src/components/chat/chat-box.tsx**
   - Complete rewrite of `sendMessage()` function
   - Removed ~200 lines of streaming code
   - Simplified loading states
   - Removed task-related UI components

### 🎯 Current API Endpoints

#### **Required**
- `POST /auth/login` - User authentication
- `POST /api/chat` - Send chat message
- `GET /api/conversations/{userId}` - List conversations
- `GET /api/conversations/{conversationId}/messages` - Load history

#### **Optional**
- `POST /auth/signup` - User registration
- `PUT /auth/user/{userId}` - Update profile
- `POST /api/conversations` - Create conversation
- `PUT /api/conversations/{conversationId}` - Update conversation
- `DELETE /api/conversations/{conversationId}` - Delete conversation
- `GET /health` - Health check

### 🔧 Technical Changes

#### **Type Definitions**
```typescript
// Before
interface ChatResponse {
  message: string;
  actions_taken: ActionResult[];
  raw_response?: string;
  conversation_id?: number;
}

// After
interface ChatResponse {
  message: string;
  raw_response?: string;
  conversation_id?: number;
}
```

```typescript
// Before
interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  actions_taken?: ActionResult[];
  created_at: string;
}

// After
interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
```

#### **API Function Signature**
```typescript
// Function remains the same
sendChatMessage(
  userId: number,
  message: string,
  smartMode?: boolean,
  conversationId?: number
): Promise<ChatResponse>
```

### 🚀 What This Template Provides

This is now a **clean, reusable chat UI template** with:

✅ Modern React + TypeScript architecture
✅ Clean authentication flow
✅ Conversation-based chat with history
✅ Responsive, animated UI
✅ Dark mode support
✅ Centralized configuration
✅ Comprehensive API documentation
✅ Type-safe API client
✅ Protected routes
✅ Development bypass mode

### 📦 Integration Steps

1. **Configure** - Update `APP_CONFIG` with your branding
2. **Backend** - Implement the 4 required endpoints
3. **Test** - Use provided cURL examples
4. **Deploy** - Build and deploy frontend

See [API_INTEGRATION.md](./API_INTEGRATION.md) for complete integration guide.

---

## Migration Guide (If Updating from v1.x)

### Backend Changes Required

1. **Remove SSE streaming endpoint** - `/api/chat/stream` no longer used
2. **Simplify chat response** - Remove `actions_taken` field
3. **Update message schema** - Remove `actions_taken` from messages table/model

### Frontend Changes

All changes are already complete in this version. No action needed.

### Database Schema Changes

If you stored `actions_taken` in your messages table:
```sql
-- Optional: Remove actions_taken column from messages
ALTER TABLE messages DROP COLUMN actions_taken;
```

---

**Version**: 2.0.0  
**Date**: 2024-01-XX  
**Status**: ✅ Complete & Ready for Integration
