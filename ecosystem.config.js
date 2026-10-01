const path = require('path');

const commonEnv = {
  PYTHONPATH: path.join(__dirname, 'backend')
};

module.exports = {
  apps: [
    {
      name: "a11ysense-backend",
      script: "python",
      args: "-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --loop asyncio",
      cwd: "./",
      env: commonEnv
    },
    {
      name: "a11ysense-frontend",
      script: "./node_modules/vite/bin/vite.js",
      cwd: "./frontend",
      env: commonEnv
    }
  ]
};
