# 🌟 Beacon

Your AI guide through documents and conversations. An intelligent assistant that searches your knowledge base while answering questions in real-time.

**Beacon** is a full-stack, AI-powered conversational agent with **Retrieval-Augmented Generation (RAG)** support, built with FastAPI, LangChain, and LLM model fallback capabilities.

## ✨ Key Features

### 🧠 Intelligent Agent
- **Multi-turn conversations** with persistent chat history
- **Automatic tool calling** - agent decides when to use available tools
- **Model fallback** - seamlessly switches from primary (Groq) to backup LLM if needed
- **Streaming responses** - real-time token streaming for responsive UX

### 📚 Retrieval-Augmented Generation (RAG)
- **Document support** - processes `.txt`, `.pdf`, `.csv`, `.xlsx`, `.xls` files
- **Smart retrieval** - agent uses semantic search to find relevant information
- **Custom descriptions** - describe your documents so the agent knows when to search them
- **FAISS embeddings** - efficient vector storage with HuggingFace embeddings
- **Per-session RAG** - enable/disable RAG independently for each conversation

### 🛠️ Built-in Tools
- **Math operations** - add, subtract, multiply, divide
- **Document retriever** - semantic search over uploaded documents
- **Final answer** - structured response with tools metadata
- **Easy extension** - simple interface to add custom tools

### 💾 Session Management
- **Persistent sessions** - SQLite database stores chat history
- **Multi-session support** - manage multiple conversations simultaneously
- **RAG configuration** - enable RAG per-session with documents path and description
- **Message tracking** - see all interactions in a session

### 🎨 Full-Stack Interface
- **Modern web UI** - responsive React-like interface (vanilla JS)
- **Real-time streaming** - watch agent think and respond live
- **Tool tracking** - see which tools were used in each response
- **Session management** - create, delete, and switch between sessions
- **Markdown rendering** - rich text support in messages

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (Vanilla JS)              │
│  - Session management    - Real-time streaming      │
│  - Chat interface        - Markdown rendering       │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/SSE
┌────────────────────▼────────────────────────────────┐
│            FastAPI Backend (Python)                 │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐    │
│  │     CustomAgentExecutor (LangChain)         │    │
│  │  - Multi-iteration agent loop               │    │
│  │  - Tool execution & response handling       │    │
│  ├─────────────────────────────────────────────┤    │
│  │     ModelFallbackMiddleware                 │    │
│  │  - Primary: Groq LLM                        │    │
│  │  - Backup: OpenAI-compatible model          │    │
│  ├─────────────────────────────────────────────┤    │
│  │     Tool Registry                           │    │
│  │  - Math tools                               │    │
│  │  - RAG retriever (FAISS + embeddings)       │    │
│  │  - Final answer tool                        │    │
│  └─────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│  SessionManager + SQLite Database                   │
│  - Chat history persistence                         │
│  - RAG configuration per session                    │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/GeneralPurposeAgent.git
   cd GeneralPurposeAgent
   ```

2. **Set up environment**
   ```bash
   cd backend
   cp .env.example .env
   ```

3. **Add your API key**
   - Edit `backend/.env` and add your Groq API key:
     ```
     GROQ_API_KEY=your_api_key_here
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the backend server**
   ```bash
   python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   python -m http.server 3000
   ```

7. **Open in browser**
   - Navigate to `http://localhost:3000`

## 📖 Usage Guide

### Basic Conversation

1. Click **"New Session"** to create a conversation
2. Type your question and press **Send**
3. Watch the agent think and respond in real-time

### Enable RAG for a Session

1. Create or select a session
2. Click the ⚙ button to open session details
3. Fill in:
   - **Documents path**: Where your documents are stored (e.g., `C:\data\docs`)
   - **RAG description**: Describe what's in your documents (e.g., "Financial planning guides including budgeting, savings, and retirement planning")
4. Click **"Enable RAG"**

### Example RAG Use Cases

#### Financial Advisor
**Documents path:** `./docs/finance`  
**Description:** "Financial planning guides covering budgeting, savings, investments, and retirement strategies"  
**Good questions:**
- "How should I save for retirement?"
- "What's a good emergency fund amount?"
- "Explain the 50/30/20 budgeting rule"

#### Company HR Bot
**Documents path:** `./docs/hr-policies`  
**Description:** "Company HR policies including vacation days, sick leave, remote work guidelines, health benefits, and employee handbook"  
**Good questions:**
- "What's our remote work policy?"
- "How many vacation days do I get?"
- "What are my health benefits?"

#### Technical Documentation
**Documents path:** `./docs/api-docs`  
**Description:** "API documentation and technical guides for system integration"  
**Good questions:**
- "How do I authenticate with the API?"
- "What endpoints are available?"
- "Show me an example request"

## 📁 Project Structure

```
GeneralPurposeAgent/
├── backend/
│   ├── agent.py              # Core agent executor
│   ├── api.py                # FastAPI endpoints
│   ├── database.py           # SQLAlchemy setup
│   ├── models.py             # DB models
│   ├── schemas.py            # Pydantic schemas
│   ├── session_manager.py    # Session handling
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Template for .env
│   ├── middleware/
│   │   └── model_fallback.py # LLM fallback logic
│   ├── tools/
│   │   ├── agent_tools.py    # final_answer tool
│   │   ├── math_tools.py     # Calculator tools
│   │   ├── rag_tools.py      # RAG & document handling
│   │   └── __init__.py       # Tool registry
│   └── rag-example/
│       └── text.txt          # Example RAG document
│
├── frontend/
│   ├── index.html            # Main page
│   ├── app.js                # Application logic
│   └── style.css             # Styling
│
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🔧 API Endpoints

### Sessions
- `POST /sessions/create` - Create new session
- `GET /sessions` - List all sessions
- `GET /sessions/{session_id}` - Get session details
- `DELETE /sessions/{session_id}` - Delete session
- `POST /sessions/{session_id}/enable-rag` - Enable RAG with documents

### Query
- `POST /query/stream` - Stream agent response (Server-Sent Events)

### Utilities
- `GET /` - API info

## 🛠️ Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional
DATABASE_URL=sqlite:///./agent_sessions.db
# For PostgreSQL: postgresql://user:password@localhost/dbname
```

### Model Configuration

Edit `backend/agent.py` to change models:

```python
model_middleware = ModelFallbackMiddleware(
    primary_model_name="qwen/qwen3-32b",      # Primary LLM
    backup_model_name="openai/gpt-oss-20b",   # Fallback LLM
    temperature=0.0                            # Model creativity (0=deterministic)
)
```

### RAG Settings

Modify vector store configuration in `backend/tools/rag_tools.py`:

```python
# Document splitting
chunk_size=1000          # Size of text chunks
chunk_overlap=200        # Overlap between chunks

# Embeddings
model_name="all-MiniLM-L6-v2"  # HuggingFace embedding model

# Retrieval
k=2                      # Number of documents to retrieve
```

## 🧪 Testing

### Manual Testing

1. Create a session with RAG enabled
2. Test with sample questions
3. Check the "🔧 Tools used" indicator in responses

### Example Test Prompts

**Math operations:**
- "What is 15 * 8?"
- "Calculate 100 / 4"

**General knowledge:**
- "What is the capital of France?"
- "Explain quantum computing"

**RAG queries** (after enabling RAG):
- "What documents are available?"
- "Summarize the key points"
- "Find information about [specific topic]"

## ⚠️ Notes on Tooling

- `final_answer` tool is currently **commented out** because the Groq-hosted model in use does not support forced tool calls. The agent now concludes a turn when it emits a response with no `tool_calls`; we execute tools when present and re-query until the model returns a plain answer.
- If you switch to a provider/model that supports `tool_choice` forcing, you can re-enable `final_answer` to enforce a single, structured termination tool call.
  
## 🔐 Security

### Important Notes

- **Never commit `.env` file** - Use `.env.example` as template
- **API keys are sensitive** - Rotate keys if accidentally exposed
- **CORS is open** - Restrict `allow_origins` in production
- **Database** - Use PostgreSQL for production, not SQLite
- **Embeddings** - Downloaded once and cached locally

### Before Production

1. Set environment-specific variables
2. Use strong database credentials
3. Restrict CORS origins
4. Enable HTTPS
5. Use environment-based configuration
6. Implement API rate limiting
7. Add authentication/authorization

## 📦 Dependencies

### Backend
- **FastAPI** - Web framework
- **LangChain** - LLM orchestration
- **ChatGroq** - Groq API integration
- **SQLAlchemy** - Database ORM
- **FAISS** - Vector similarity search
- **HuggingFace** - Embeddings
- **python-dotenv** - Environment configuration

### Frontend
- Vanilla JavaScript (no framework required)
- CSS3 + Flexbox
- Fetch API + Server-Sent Events

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🎯 Roadmap

- [ ] Web-based RAG document uploader
- [ ] Multi-language support
- [ ] Custom tool creation UI
- [ ] Conversation export (JSON/PDF)
- [ ] Advanced analytics dashboard
- [ ] OpenAI API compatibility
- [ ] Docker containerization
- [ ] Unit and integration tests

## 🆘 Troubleshooting

### API key not found
```
Error: GROQ_API_KEY not found
```
**Solution:** Check that `.env` file exists in `backend/` directory with your key

### Vector store not found
```
Error: Vector store not found at path
```
**Solution:** First create the vector store by enabling RAG; documents will be processed automatically

### Port already in use
```
Error: Address already in use
```
**Solution:** Change port in startup command: `--port 8001`

### Database locked
```
Error: database is locked
```
**Solution:** Close other instances of the app; SQLite doesn't support concurrent access well

## 📧 Support

For issues, questions, or suggestions:
- Open a GitHub issue
- Check existing issues for solutions
- Review the project documentation

## 🙏 Acknowledgments

- [Groq](https://groq.com) - Fast LLM inference
- [LangChain](https://langchain.com) - LLM orchestration
- [FastAPI](https://fastapi.tiangolo.com) - Modern web framework
- [FAISS](https://ai.meta.com/tools/faiss/) - Vector search
- [HuggingFace](https://huggingface.co) - ML models


