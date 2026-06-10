const path = require('path');

// Helper to generate service configs for an environment
const createServices = (envName, venvPath, gatewayPort, agentPort, reportingPort, crawlerPort, analyzerPort, llmPort) => {
  const commonEnv = {
    ENV_FILE: `.env.${envName}`,
    APP_ENV: envName,
    PYTHONPATH: path.join(__dirname, 'backend'),
    AGENT_SERVICE_URL: `http://localhost:${agentPort}`,
    REPORTING_SERVICE_URL: `http://localhost:${reportingPort}`,
    CRAWLER_SERVICE_URL: `http://localhost:${crawlerPort}`,
    ANALYZER_SERVICE_URL: `http://localhost:${analyzerPort}`,
    LLM_SERVICE_URL: `http://localhost:${llmPort}`,
    ALLURE_RESULTS_DIR: path.join(__dirname, 'backend', 'storage', 'reports', 'allure-results', envName)
  };

  const services = [
    { name: `${envName}-gateway`, script: `backend/${venvPath}/bin/uvicorn`, args: `app.main:app --host 0.0.0.0 --port ${gatewayPort} --loop asyncio`, cwd: "./backend/services/gateway" },
    { name: `${envName}-agent`, script: `backend/${venvPath}/bin/uvicorn`, args: `app.main:app --host 0.0.0.0 --port ${agentPort} --loop asyncio`, cwd: "./backend/services/agent" },
    { name: `${envName}-reporting`, script: `backend/${venvPath}/bin/uvicorn`, args: `app.main:app --host 0.0.0.0 --port ${reportingPort} --loop asyncio`, cwd: "./backend/services/reporting" },
    { name: `${envName}-crawler`, script: `backend/${venvPath}/bin/uvicorn`, args: `app.main:app --host 0.0.0.0 --port ${crawlerPort} --loop asyncio`, cwd: "./backend/services/crawler" },
    { name: `${envName}-analyzer`, script: `backend/${venvPath}/bin/uvicorn`, args: `app.main:app --host 0.0.0.0 --port ${analyzerPort} --loop asyncio`, cwd: "./backend/services/analyzer" },
    { name: `${envName}-llm`, script: `backend/${venvPath}/bin/uvicorn`, args: `app.main:app --host 0.0.0.0 --port ${llmPort} --loop asyncio`, cwd: "./backend/services/llm" },
  ];

  return services.map(s => ({ ...s, env: commonEnv, autorestart: true, max_memory_restart: '1G' }));
};

module.exports = {
  apps: [
    ...createServices('dev', 'venv-dev', 8000, 8001, 8002, 8003, 8004, 8005),
    ...createServices('qa', 'venv-qa', 8100, 8101, 8102, 8103, 8104, 8105),
    ...createServices('prod', 'venv-prod', 8200, 8201, 8202, 8203, 8204, 8205)
  ]
};
