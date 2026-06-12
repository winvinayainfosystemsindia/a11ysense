import asyncio
import sys

# Windows proactor loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment, get_cors_origins
setup_environment()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router as reporting_router
from app.services.worker import reporting_worker

app = FastAPI(title="A11ySense AI Reporting Service")

from common.exceptions.handler import setup_global_exception_handler
setup_global_exception_handler(app, "reporting-service")

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# Mount routes
app.include_router(reporting_router)


@app.on_event("startup")
async def startup_event():
    """Start background Reporting Stream listener thread on service launch."""
    reporting_worker.start()
