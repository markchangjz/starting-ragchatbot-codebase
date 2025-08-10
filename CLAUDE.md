# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Full stack start**: `./run.sh` (requires `chmod +x run.sh` first)
- **Backend only**: `cd backend && uv run uvicorn app:app --reload --port 8000`
- **Dependencies**: `uv sync` (installs all Python dependencies)

### Environment Setup
- Create `.env` file with `ANTHROPIC_API_KEY=your_key_here`
- Python 3.13+ required
- Uses `uv` for package management (not pip)

## Architecture Overview

This is a Retrieval-Augmented Generation (RAG) chatbot system with the following structure:

### Core Components
- **RAGSystem** (`rag_system.py`): Main orchestrator that coordinates all components
- **DocumentProcessor** (`document_processor.py`): Converts course documents into structured chunks
- **VectorStore** (`vector_store.py`): ChromaDB-based semantic search using sentence transformers
- **AIGenerator** (`ai_generator.py`): Anthropic Claude integration with tool calling
- **SessionManager** (`session_manager.py`): Conversation history tracking

### Data Models (`models.py`)
- **Course**: Contains title, lessons, and metadata
- **Lesson**: Individual lesson with title and optional link
- **CourseChunk**: Text chunks for vector storage with course/lesson references

### Tool System
- **ToolManager** (`search_tools.py`): Manages AI tool calling capabilities
- **CourseSearchTool**: Semantic search tool that Claude can invoke
- AI can search course materials using tools rather than manual retrieval

### API Layer (`app.py`)
- FastAPI application serving both API and frontend
- Key endpoints:
  - `POST /api/query`: Process user questions
  - `GET /api/courses`: Get course statistics
- Serves static frontend files from `/frontend/`

### Configuration (`config.py`)
- Centralized settings with environment variable support
- Default model: `claude-sonnet-4-20250514`
- ChromaDB path: `./chroma_db`
- Document chunking: 800 chars with 100 char overlap

## Key Implementation Details

### Document Processing Flow
1. Documents in `/docs/` are auto-loaded on startup
2. Each document becomes a Course with extracted lessons
3. Content is chunked and stored in ChromaDB for semantic search
4. Course metadata stored separately for analytics

### Query Processing Flow
1. User query sent to RAGSystem
2. AI generates response using available tools (CourseSearchTool)
3. AI automatically searches relevant course content as needed
4. Response includes both answer and source references
5. Session history maintained for context

### Frontend Integration
- Simple HTML/JS frontend in `/frontend/` directory
- API calls to backend for query processing
- FastAPI serves both API and static files from single server

## Development Notes

- No test framework currently configured
- Uses ChromaDB for local vector storage (no external dependencies)
- Course documents supported: PDF, DOCX, TXT
- Conversation history limited to last 2 exchanges per session