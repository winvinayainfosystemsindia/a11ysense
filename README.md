# A11ySense AI — Accessibility Test Automation Platform

**A11ySense AI** is an enterprise-grade accessibility test automation platform built for testing Web Pages and Web Applications against **WCAG 2.2 Level A and AA** compliance standards.

Powered by a unified **FastAPI Monolith** backend, **Playwright** browser automation, **Claude + Gemini AI** auditing agents, and a modern **React + Vite** dashboard.

---

## Tech Stack & Monolith Architecture

A11ySense AI operates as a unified, high-performance monolith architecture designed for maximum execution speed, zero microservice latency, and cross-platform compatibility (Windows & Linux).

- **Backend Monolith (`backend/app/main.py`)**: Unified FastAPI server handling Authentication, Project Management, Credential Encryption, Web Crawling, WCAG 2.2 Auditing, and Excel Report Generation.
- **Frontend Dashboard (`frontend/`)**: Modern React dashboard built with TypeScript, Vite, Material UI (MUI), and TanStack Router.
- **AI Audit Router**: Primary LLM: **Claude** (`anthropic` SDK), Fallback LLM: **Gemini** (`google.generativeai` SDK).
- **Caching & Queue**: Cross-platform `diskcache` (SQLite-backed) for persistent state management without Redis dependencies.
- **Database**: PostgreSQL metadata store (SQLAlchemy ORM + automatic table creation).

---

## Project Structure

```text
a11ysense/
├── backend/                  # Server-side FastAPI Monolith Application
│   ├── app/                  # Main application source
│   │   ├── api/              # API Endpoints (auth, projects, credentials, audit, reports, dashboard)
│   │   ├── core/             # Core Engine (crawler, auditor agents, skills, LLM router, reporting)
│   │   ├── repository/       # Database repositories
│   │   ├── main.py           # Single FastAPI application entry point
│   │   ├── cache.py          # DiskCache wrapper (Windows & Linux compatible)
│   │   └── task_queue.py     # In-process async background task runner
│   ├── common/               # Shared database models, connection, auth deps & schemas
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Backend environment variables template
│   └── .env                  # Backend active environment configuration
├── frontend/                 # React + TypeScript Vite Dashboard
│   ├── src/                  # React components, pages, routes, and state store
│   ├── .env.example          # Frontend environment variables template
│   └── .env                  # Frontend active environment configuration
├── .gitignore
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 15+**

---

### Step 1: Database Setup
Ensure PostgreSQL is running locally on port `5432` with a database named `a11ysense`:
```sql
CREATE DATABASE a11ysense;
```

---

### Step 2: Backend Setup & Execution

1. **Navigate to the `backend/` directory**:
   ```bash
   cd backend
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and set your API keys and PostgreSQL credentials:
   ```env
   LLM_PROVIDER=claude
   ANTHROPIC_API_KEY=sk-ant-api03-...
   GEMINI_API_KEY=AIzaSy...

   POSTGRES_SERVER=localhost
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=12345
   POSTGRES_DB=a11ysense
   POSTGRES_PORT=5432
   ```

3. **Install Dependencies & Playwright Browsers**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Run the Monolith Backend**:
   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The backend API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).*

---

### Step 3: Frontend Setup & Execution

1. **Navigate to the `frontend/` directory**:
   ```bash
   cd frontend
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

3. **Install Dependencies & Launch Dev Server**:
   ```bash
   npm install
   npm run dev
   ```
   *Access the web application at [http://localhost:5173](http://localhost:5173).*

---

## Application Workflow

1. **Authentication**: Sign up or log in securely (`admin@a11y.com` / `password` seeded by default).
2. **Project Creation**: Create a project and select target type:
   - 🌐 **Web Page**: Public domain website crawl and audit.
   - 💻 **Web Application**: Public + Auth-protected portal audit with saved test credentials.
3. **Crawl & Discovery**: Page discovery engine maps public and authenticated routes.
4. **WCAG 2.2 Audit Execution**: Scans for 56 success criteria across Level A and AA using automated Axe-core + Screen Reader persona AI refinement.
5. **Executive Reports**: Download 3-sheet formatted `.xlsx` report containing:
   - **Sheet 1: Defect Report** (Dark Red header `#8B0000`)
   - **Sheet 2: Test Case Report** (Dark Blue header `#1A237E`)
   - **Sheet 3: WCAG Criteria Reference** (Light Blue header `#1565C0`)

---

## License
Proprietary Corporate License Agreement. See [LICENSE](LICENSE) for full terms.

Copyright (c) 2026 WinVinaya InfoSystems India. All rights reserved.