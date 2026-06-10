# A11ySense AI: OpenClaw Powered Accessibility Auditing

A11ySense AI is an enterprise-grade, microservices-based accessibility testing platform. It leverages **OpenClaw** for autonomous agentic auditing, **FastAPI** for high-performance backend services, and **React/MUI** for a modern, accessible user interface.

## Tech Stack

- **Backend**: FastAPI, Pydantic, Python 3.10+
- **Agent Framework**: OpenClaw (Autonomous AI Agents)
- **Frontend**: React, TypeScript, Material UI (MUI)
- **Database**: PostgreSQL (for metadata), Redis (for task queuing)
- **Reporting**: Allure Report
- **Orchestration**: Docker, Kubernetes

## Project Structure

```text
A11ySense_AI/
├── backend/                # Server-side microservices
│   ├── common/             # Shared Pydantic models & utils
│   └── services/           # Independent services (Gateway, Crawler, etc.)
├── frontend/               # React + TS + MUI Dashboard
├── infra/                  # Docker & K8s configurations
├── scripts/                # Development & Ops scripts
└── docs/                   # Architecture & API documentation
```

## Getting Started

1. **Prerequisites**: Docker, Python 3.10+, Node.js 18+
2. **Installation**:
   ```bash
   # Clone and setup (Instructions coming soon)
   ```
3. **Running Locally**:
   ```bash
   docker-compose up --build
   ```

## License
MIT