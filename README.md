# RAG Education System

A complete RAG (Retrieval-Augmented Generation) education system with hierarchical document processing, powered by **Gemini 2.5 Flash**.

## Features

- 📚 **Course Management**: Create and organize courses with hierarchical units
- 📄 **PDF Upload**: Upload PDFs and automatically process them into searchable chunks
- 🔍 **RAG-powered Chat**: Ask questions and get AI-generated answers based on your course materials
- 🎯 **Intent Classification**: Automatically adjusts retrieval strategy based on query type
- 💾 **Persistent Storage**: ChromaDB for vector storage, SQLite for data

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy + SQLite
- ChromaDB (Vector Store)
- Google Gemini 2.5 Flash (LLM)
- PyPDF2 (PDF Processing)

### Frontend
- React 18 + Vite
- TailwindCSS
- React Query
- React Router

## Quick Start

### 1. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key to .env
# Edit backend/.env and set GEMINI_API_KEY=your_key_here

# Run backend
python -m app.main
```

The backend API will be available at `http://localhost:8000`

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 3. Using Docker (Alternative)

```bash
# Set your Gemini API key
export GEMINI_API_KEY=your_key_here

# Run with Docker Compose
docker-compose up --build
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login/Register user

### Courses
- `GET /api/courses/` - Get all courses
- `POST /api/courses/` - Create a course
- `POST /api/courses/{id}/upload` - Upload PDF document
- `GET /api/courses/{id}/structure` - Get course structure
- `POST /api/courses/{id}/units` - Create a unit

### Chat
- `POST /api/chat/session` - Create chat session
- `POST /api/chat/message` - Send message (non-streaming)
- `POST /api/chat/message/stream` - Send message (streaming)
- `GET /api/chat/sessions` - Get all sessions
- `GET /api/chat/sessions/{id}/messages` - Get session messages

## Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite:///./education.db
SECRET_KEY=your-secret-key
UPLOAD_DIR=./uploads
CHROMA_DIR=./storage/chroma_db
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
rag-education-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── courses.py
│   │   │   └── chat.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── gemini_service.py
│   │   │   ├── vector_store.py
│   │   │   ├── document_processor.py
│   │   │   └── rag_service.py
│   │   ├── database.py
│   │   └── main.py
│   ├── storage/
│   ├── uploads/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── ChatInterface.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Usage

1. **Login**: Enter your email to create/access your account
2. **Create Course**: Click "New Course" and add a name/description
3. **Upload PDF**: Click "Upload" on a course card to add materials
4. **Chat**: Click "Chat" to ask questions about your course materials

## License

MIT
