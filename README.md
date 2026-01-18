# 📚 RAG Education System

An AI-powered learning platform that lets you upload study materials and chat with an intelligent tutor that understands your content. Built with **Gemini 2.5 Flash** and RAG (Retrieval-Augmented Generation) technology.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-green.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)

## ✨ Features

- 🔐 **Authentication** - Email/password + Google OAuth sign-in
- 📚 **Course Management** - Create and organize multiple courses
- 📄 **PDF Upload** - Upload PDFs (up to 10MB) and auto-process into searchable chunks
- 🤖 **AI-Powered Chat** - Ask questions and get accurate answers from your materials
- 🧠 **Smart Fallback** - When content isn't in your docs, the AI uses general knowledge
- 📐 **Math Support** - LaTeX/KaTeX rendering for mathematical formulas (λ, π, etc.)
- 🌙 **Dark Mode** - Beautiful dark-themed UI
- 🔒 **Production Ready** - JWT auth, rate limiting, PostgreSQL support

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, TailwindCSS, React Query, React Router |
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL (production) / SQLite (development) |
| **Vector Store** | ChromaDB with Gemini embeddings |
| **AI** | Google Gemini 2.5 Flash |
| **Auth** | JWT tokens, bcrypt, Google OAuth 2.0 |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 16 (optional, for production)
- [Gemini API Key](https://aistudio.google.com/app/apikey)

### Option 1: Local Development (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/rag-education-system.git
cd rag-education-system

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY

# Start everything with one command
./start.sh
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Docker

```bash
# Set your Gemini API key
export GEMINI_API_KEY=your_key_here

# Run with Docker Compose
docker-compose up --build
```

- Frontend: http://localhost (port 80)
- Backend: http://localhost:8000

## 🐳 Docker Explained

Docker packages your application into containers - isolated environments that include everything needed to run your code. This ensures "it works on my machine" becomes "it works everywhere."

### Backend Dockerfile (`backend/Dockerfile`)
```dockerfile
FROM python:3.12-slim        # Start with lightweight Python image
WORKDIR /app                  # Set /app as working directory
COPY requirements.txt .       # Copy dependencies file first
RUN pip install ...           # Install Python packages
COPY . .                      # Copy all application code
CMD ["uvicorn", ...]          # Command to start FastAPI server on port 8000
```

**What it does**: Creates a container with Python, installs your dependencies, copies your code, and runs the FastAPI server.

### Frontend Dockerfile (`frontend/Dockerfile`)
```dockerfile
# Stage 1: Build the React app
FROM node:18-alpine AS build  # Node.js to build the app
RUN npm install               # Install npm packages
RUN npm run build             # Build static HTML/CSS/JS files

# Stage 2: Serve with Nginx
FROM nginx:alpine             # Lightweight web server
COPY --from=build /app/dist   # Copy built files from stage 1
CMD ["nginx", ...]            # Serve static files on port 80
```

**What it does**: Uses a "multi-stage build" - first builds your React app, then copies only the built files to a tiny Nginx server. This makes the final image much smaller (~20MB vs ~1GB).

### docker-compose.yml
```yaml
services:
  backend:   # FastAPI on port 8000
  frontend:  # Nginx on port 80
```

**What it does**: Orchestrates both containers, sets up networking between them, and manages environment variables and data volumes.

## ☁️ Production Deployment (Free)

### Recommended Stack

| Service | Platform | Cost |
|---------|----------|------|
| Frontend | Vercel | Free |
| Backend | Render | Free (750h/mo) |
| Database | Supabase | Free (500MB) |

### Step 1: Supabase (PostgreSQL Database)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project (save the password!)
3. Go to **Settings → Database → Connection string (URI)**
4. Copy the connection string

### Step 2: Render (Backend API)

1. Create account at [render.com](https://render.com)
2. **New → Web Service → Connect GitHub repo**
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables**:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Your Supabase connection string |
| `GEMINI_API_KEY` | Your Gemini API key |
| `SECRET_KEY` | Generate: `openssl rand -hex 32` |
| `GOOGLE_CLIENT_ID` | Your Google OAuth Client ID |
| `CORS_ORIGINS_STR` | `https://your-app.vercel.app` |
| `ENVIRONMENT` | `production` |

### Step 3: Vercel (Frontend)

1. Create account at [vercel.com](https://vercel.com)
2. **Import GitHub repo**
3. Configure:
   - **Framework**: Vite
   - **Root Directory**: `frontend`
4. Add **Environment Variables**:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://your-backend.onrender.com` |
| `VITE_GOOGLE_CLIENT_ID` | Your Google OAuth Client ID |

### Step 4: Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create **OAuth 2.0 Client ID**
3. Add to **Authorized JavaScript origins**:
   - `http://localhost:5173`
   - `https://your-app.vercel.app`

## 📁 Project Structure

```
rag-education-system/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes (auth, courses, chat)
│   │   ├── core/          # Config, security, JWT
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── services/      # Business logic (RAG, vectors, Gemini)
│   │   └── utils/         # Logging utilities
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Container build instructions
│   └── .env              # Environment variables
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route pages (Login, Dashboard, Chat)
│   │   ├── services/      # API client (axios)
│   │   └── lib/           # Utilities
│   ├── package.json       # Node dependencies
│   └── Dockerfile         # Container build instructions
├── docker-compose.yml     # Multi-container orchestration
├── render.yaml            # Render deployment config
├── start.sh              # Dev start script
└── stop.sh               # Dev stop script
```

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login with email/password |
| POST | `/api/auth/google` | Login with Google OAuth |

### Courses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/courses/` | Get all courses |
| POST | `/api/courses/` | Create a course |
| DELETE | `/api/courses/{id}` | Delete a course |
| POST | `/api/courses/{id}/upload` | Upload PDF documents |
| GET | `/api/courses/{id}/documents` | Get course documents |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/message` | Send message, get AI response |
| GET | `/api/chat/sessions` | Get chat sessions |
| GET | `/api/chat/sessions/{id}/messages` | Get messages |

## 🔧 Environment Variables

### Backend (.env)
```env
# Required
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-256-bit-secret-key

# Optional
GOOGLE_CLIENT_ID=your-google-oauth-client-id
CORS_ORIGINS_STR=http://localhost:5173,https://your-app.vercel.app
ENVIRONMENT=development  # or production
DEBUG=true
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id
```

## 🎓 Student Offers (Free Credits)

Get free cloud credits with your .edu email:

| Program | Benefit | Link |
|---------|---------|------|
| **GitHub Student Pack** | $200+ in credits | [education.github.com/pack](https://education.github.com/pack) |
| **Google Cloud** | $300 free credit | [cloud.google.com/edu](https://cloud.google.com/edu) |
| **Azure for Students** | $100 free credit | [azure.microsoft.com/free/students](https://azure.microsoft.com/free/students) |

## 📖 Usage

1. **Sign Up/Login**: Create account with email or Google
2. **Create Course**: Click "New Course" and add a name/description  
3. **Upload PDFs**: Click on a course, then upload your study materials
4. **Chat**: Ask questions about your documents - the AI will answer based on your content

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ using Gemini 2.5 Flash & RAG Technology
