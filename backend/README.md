# Beacon Agent API

A FastAPI-based conversational AI agent with session management, streaming responses, and RAG capabilities.

## Project Structure

```
backend/
├── api.py                  # FastAPI application with all endpoints
├── agent.py               # Agent executor and callback handler
├── database.py            # Database configuration
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas for request/response
├── session_manager.py     # Session management logic
├── main.py                # Original standalone script (kept for reference)
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (GROQ_API_KEY)
```

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**
Create a `.env` file with:
```
GROQ_API_KEY=your_groq_api_key_here
```

3. **Run the API:**
```bash
python api.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Create Session
**POST** `/sessions/create`

Creates a new conversation session.

**Response:**
```json
{
  "session_id": "uuid",
  "message": "Session created successfully"
}
```

### 2. Get Session
**GET** `/sessions/{session_id}`

Retrieves session details including full chat history.

**Response:**
```json
{
  "id": "uuid",
  "created_at": "2026-01-06T...",
  "updated_at": "2026-01-06T...",
  "rag_enabled": false,
  "rag_documents_path": null,
  "messages": [
    {
      "id": "uuid",
      "role": "human",
      "content": "Hello",
      "created_at": "2026-01-06T..."
    }
  ]
}
```

### 3. List All Sessions
**GET** `/sessions`

Returns all sessions.

### 4. Delete Session
**DELETE** `/sessions/{session_id}`

Deletes a session and all its messages.

### 5. Enable RAG
**POST** `/sessions/{session_id}/enable-rag`

Enables RAG for a session with a document path.

**Request:**
```json
{
  "documents_path": "/path/to/documents"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "message": "RAG enabled with documents from: /path/to/documents"
}
```

### 6. Stream Query (Main Endpoint)
**POST** `/query/stream`

Sends a query to the agent and streams the response using Server-Sent Events (SSE).

**Request:**
```json
{
  "query": "What is 10 + 10 divided by 20 then multiplied by 15?",
  "session_id": "uuid"
}
```

**Response (SSE Stream):**
```
data: {"type": "content", "content": "Let me calculate that..."}

data: {"type": "tool_call", "tool_name": "add_numbers"}

data: {"type": "tool_args", "args": "{\"x\": 10, \"y\": 10}"}

data: {"type": "step_end"}

data: {"type": "final_answer", "answer": "The answer is 15", "tools_used": ["add_numbers", "divide_numbers", "multiply_numbers"]}

data: {"type": "done"}
```

## Usage Example

### Using Python:

```python
import requests
import json

# 1. Create session
response = requests.post("http://localhost:8000/sessions/create")
session_id = response.json()["session_id"]
print(f"Session ID: {session_id}")

# 2. Enable RAG (optional)
requests.post(
    f"http://localhost:8000/sessions/{session_id}/enable-rag",
    json={"documents_path": "/path/to/docs"}
)

# 3. Stream query
response = requests.post(
    "http://localhost:8000/query/stream",
    json={
        "query": "What is 10 + 10?",
        "session_id": session_id
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(data)
```

### Using cURL:

```bash
# Create session
curl -X POST http://localhost:8000/sessions/create

# Enable RAG
curl -X POST http://localhost:8000/sessions/{session_id}/enable-rag \
  -H "Content-Type: application/json" \
  -d '{"documents_path": "/path/to/docs"}'

# Stream query
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 10 + 10?", "session_id": "your-session-id"}'
```

## Features

- ✅ **Session Management**: Persistent conversations stored in SQLite
- ✅ **Streaming Responses**: Real-time SSE streaming with tool call visibility
- ✅ **RAG Support**: Enable RAG per session with custom document paths
- ✅ **Chat History**: Full conversation history maintained per session
- ✅ **Tool Calling**: Built-in math tools (add, subtract, multiply, divide)
- ✅ **Database Persistence**: SQLAlchemy ORM with SQLite

## Database

Sessions and messages are stored in `agent_sessions.db` (SQLite).

**Sessions Table:**
- id (primary key)
- created_at
- updated_at
- rag_enabled
- rag_documents_path

**Messages Table:**
- id (primary key)
- session_id (foreign key)
- role (human/ai)
- content
- created_at

## Next Steps for RAG Implementation

The RAG endpoint is ready to accept document paths. To implement RAG:

1. Add a document loader in `agent.py`
2. Create vector embeddings from documents
3. Add retrieval logic before agent invocation
4. Pass retrieved context to the agent's prompt

Example:
```python
if session.rag_enabled and session.rag_documents_path:
    # Load documents from path
    # Create embeddings
    # Retrieve relevant docs
    # Add to context
```

## License

MIT
