# ⚡ CodeCraft AI

**Lovable-style AI Coding Platform** — built from scratch with FastAPI, Streamlit, Bootstrap, and multi-model AI support.

## Features

| Feature | Description |
|---------|-------------|
| 💬 **Multi-Model Chat** | Stream conversations with Claude, Gemini & GLM |
| 📝 **Code Editor** | In-browser editor with syntax highlighting, run, lint, format |
| 🚀 **Project Generator** | Describe a project, get complete code with files |
| 🐙 **GitHub Integration** | Fetch repos, analyze code, deploy workspaces |
| 📷 **Image Analysis** | Upload screenshots → AI analyzes and suggests code |
| 🔍 **Web Search** | Search docs and examples without leaving the app |
| 🧪 **Test Runner** | Run pytest/npm test directly from the UI |
| 💾 **Auto Save** | Session state persisted to Supabase |

## Tech Stack

- **Frontend**: Streamlit + Bootstrap 5 + Custom CSS
- **Backend**: FastAPI + Uvicorn
- **AI**: Claude (Anthropic), Gemini (Google), GLM (ZhipuAI)
- **Database**: Supabase (PostgreSQL)
- **GitHub**: PyGitHub

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd custom-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start (both backend + frontend)
python main.py

# Or start separately:
python main.py api   # FastAPI on :8000
python main.py ui    # Streamlit on :8501
```

## URLs

| Service | URL |
|---------|-----|
| Streamlit UI | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## Environment Variables

```env
# AI Models
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
ZHIPUAI_API_KEY=your_key

# GitHub
GITHUB_TOKEN=your_token

# Supabase (optional)
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

## Supabase Schema

```sql
-- Run in Supabase SQL editor
create table projects (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  created_at timestamptz default now(),
  updated_at timestamptz
);

create table sessions (
  id uuid default gen_random_uuid() primary key,
  title text,
  project_id uuid references projects(id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table messages (
  id uuid default gen_random_uuid() primary key,
  session_id uuid references sessions(id),
  project_id uuid references projects(id),
  role text not null,
  content text not null,
  model text,
  created_at timestamptz default now()
);

create table auto_saves (
  session_id uuid primary key,
  state jsonb,
  saved_at timestamptz default now()
);
```

## Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat/message` | Single chat response |
| POST | `/api/chat/stream` | Streaming chat (SSE) |
| POST | `/api/chat/generate-project` | Generate full project |
| GET | `/api/files/list` | List workspace files |
| GET | `/api/files/read` | Read file content |
| POST | `/api/files/write` | Write file |
| POST | `/api/files/run` | Execute code snippet |
| POST | `/api/files/test` | Run test suite |
| GET | `/api/github/repos` | List GitHub repos |
| POST | `/api/github/deploy` | Deploy to GitHub |
| POST | `/api/images/upload` | Upload + analyze image |

## Architecture

```
custom-agent/
├── main.py                  # Entry point (starts both servers)
├── app/
│   ├── streamlit_app.py     # Streamlit UI (Lovable-style)
│   ├── config.py            # Settings from .env
│   ├── ai/
│   │   ├── agent.py         # Main coding agent
│   │   ├── claude_client.py # Anthropic Claude
│   │   ├── gemini_client.py # Google Gemini
│   │   └── glm_client.py    # ZhipuAI GLM
│   ├── tools/
│   │   ├── file_tools.py    # File CRUD
│   │   ├── github_tools.py  # GitHub API
│   │   ├── search_tools.py  # Web search
│   │   ├── image_tools.py   # Image processing
│   │   └── test_tools.py    # Code execution & testing
│   ├── api/
│   │   ├── server.py        # FastAPI app
│   │   └── routes/          # chat, files, github, images
│   └── db/
│       └── supabase_client.py
├── static/css/custom.css
├── tests/
└── workspace/               # Generated project files
```
