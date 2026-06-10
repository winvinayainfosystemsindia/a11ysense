import asyncio
import sys

# standard Windows loop patch for subprocesses and sockets
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment, get_cors_origins
# Initialize central configuration loader
setup_environment()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as llm_router

app = FastAPI(title="A11ySense AI Central LLM Service")

from common.exceptions.handler import setup_global_exception_handler
setup_global_exception_handler(app, "llm-service")

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(llm_router)
