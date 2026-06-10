const path = require('path');

const commonEnv = {
  PYTHONPATH: path.join(__dirname, 'backend'),
  AGENT_SERVICE_URL: "http://localhost:8001",
  REPORTING_SERVICE_URL: "http://localhost:8002",
  CRAWLER_SERVICE_URL: "http://localhost:8003",
  ANALYZER_SERVICE_URL: "http://localhost:8004",
  LLM_SERVICE_URL: "http://localhost:8005",
  ALLURE_RESULTS_DIR: path.join(__dirname, 'backend', 'storage', 'reports', 'allure-results')
};

module.exports = {
  apps: [
    {
      name: "gateway",
      script: "python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop asyncio",
      cwd: "./backend/services/gateway",
      env: commonEnv
    },
    {
      name: "agent",
      script: "python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8001 --loop asyncio",
      cwd: "./backend/services/agent",
      env: commonEnv
    },
    {
      name: "reporting",
      script: "python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8002 --loop asyncio",
      cwd: "./backend/services/reporting",
      env: commonEnv
    },
    {
      name: "crawler",
      script: "python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8003 --loop asyncio",
      cwd: "./backend/services/crawler",
      env: commonEnv
    },
    {
      name: "analyzer",
      script: "python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8004 --loop asyncio",
      cwd: "./backend/services/analyzer",
      env: commonEnv
    },
    {
      name: "llm",
      script: "python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8005 --loop asyncio",
      cwd: "./backend/services/llm",
      env: commonEnv
    },
    {
      name: "frontend",
      script: "./node_modules/vite/bin/vite.js",
      cwd: "./frontend",
      env: commonEnv
    }
  ]
};
