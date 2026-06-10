# A11ySense AI: OpenClaw Powered Accessibility Auditing

A11ySense AI is an enterprise-grade, microservices-based accessibility testing platform. It leverages **OpenClaw** for autonomous agentic auditing, **FastAPI** for high-performance backend services, and **React + Vite** for a modern, responsive user interface.

## Tech Stack & Architecture

A11ySense AI is designed around a distributed microservices architecture to ensure scalability, fault isolation, and component reusability:

- **Gateway Service (Port `8000`)**: The centralized entrypoint that routes requests, handles JWT authentication, and manages user/organization profiles.
- **Agent Service (Port `8001`)**: The OpenClaw-powered agentic orchestrator that conducts autonomous, page-by-page accessibility audits using Playwright.
- **Reporting Service (Port `8002`)**: Compiles raw accessibility issues, manages reports, and serves Allure-compatible report data.
- **Crawler Service (Port `8003`)**: Traverses and maps target website domains to automatically discover pages for audit campaigns.
- **Analyzer Service (Port `8004`)**: De-duplicates violations, runs false-positive heuristics, computes 0-100 scores, and tracks historical regression trends.
- **LLM Service (Port `8005`)**: Centralized LLM gateway managing prompt compression, token pricing estimation, response caching, and model fallbacks (configured for Groq by default).
- **Frontend (Port `5173` / `3000`)**: A premium React dashboard built with TypeScript and Vite.
- **Database & Storage**: PostgreSQL (metadata store), Redis (task queuing), and local file-system reports storage.

---

## Project Structure

```text
a11ysense/
├── backend/                  # Server-side microservices
│   ├── common/               # Shared Pydantic schemas, database configurations, and utils
│   ├── services/             # Independent FastAPI microservices
│   │   ├── gateway/
│   │   ├── agent/
│   │   ├── reporting/
│   │   ├── crawler/
│   │   ├── analyzer/
│   │   └── llm/
│   ├── requirements.txt      # Master requirements file for the backend services
│   ├── install.ps1           # Windows dependency installer script
│   └── install.sh            # Unix dependency installer script
├── frontend/                 # React + TypeScript Vite dashboard
├── deploy/                   # Production deployment helper scripts
├── docs/                     # Comprehensive architecture and deployment guides
├── nginx/                    # Configuration files for reverse proxy setup
├── docker-compose.yml        # Multi-container local orchestration configuration
├── ecosystem.config.js       # PM2 process file for local execution
├── start_all.bat             # Single-click Windows start script (uses PM2)
└── stop_all.bat              # Single-click Windows stop script
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Redis**
- **Java 11+** (Optional, required to view Allure reports)

---

### Option A: Local Run via PM2 (Recommended for Windows)

This project includes pre-configured utility scripts to run all services concurrently using **PM2**.

1. **Configure Environment Variables**:
   Copy `.env.dev.example` into a new `.env` file in the root folder and add your LLM API Key:
   ```bash
   copy .env.dev.example .env
   ```
   *Make sure your PostgreSQL details are correctly specified in your `.env`.*

2. **Install Backend Dependencies**:
   Open a terminal in the `backend/` folder and run:
   ```powershell
   pip install -r requirements.txt
   playwright install
   ```

3. **Install Frontend Dependencies**:
   Open a terminal in the `frontend/` folder and run:
   ```bash
   npm install
   ```

4. **Start All Services**:
   Simply run the start batch file in the project root:
   ```bash
   .\start_all.bat
   ```
   *This automatically installs PM2 globally and launches the gateway, microservices, and frontend.*

5. **Stop All Services**:
   ```bash
   .\stop_all.bat
   ```

---

### Option B: Local Run via Docker Compose

If you have Docker and Docker Compose installed:

1. Build and spin up the microservices, frontend, PostgreSQL, and Redis:
   ```bash
   docker-compose up --build
   ```

---

## Further Documentation

Detailed architecture analysis and guides can be found in the `docs/` folder:
- [Architecture Analysis](file:///c:/External-projects/WinVinaya/a11ysense/docs/architecture_analysis.md)
- [Local Deployment Guide](file:///c:/External-projects/WinVinaya/a11ysense/docs/local_deployment_guide.md)
- [EC2 Deployment Guide](file:///c:/External-projects/WinVinaya/a11ysense/docs/ec2-deployment-guide.md)
- [CI/CD Workflow Guide](file:///c:/External-projects/WinVinaya/a11ysense/docs/cicd-workflow-guide.md)

## License
This project is licensed under a proprietary **Corporate License Agreement**. See the [LICENSE](file:///c:/External-projects/WinVinaya/a11ysense/LICENSE) file for the full terms and restrictions.

Copyright (c) 2026 WinVinaya InfoSystems India. All rights reserved.