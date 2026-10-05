import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.controllers import router
from app.controllers.system import router as system_router
from app.database import Base, engine
from app.repositories import ConflictError
from app.security import AuthSettings
from app.services import WorkflowError
from app.services.auth import AuthenticationError


@asynccontextmanager
async def lifespan(application: FastAPI):
    if application.state.auth_settings is None:
        application.state.auth_settings = AuthSettings.from_env()
    Base.metadata.create_all(bind=engine)
    yield


async def workflow_error_handler(request: Request, error: WorkflowError):
    return JSONResponse(status_code=error.status_code, content={"detail": error.message})


async def conflict_error_handler(request: Request, error: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(error)})


async def authentication_error_handler(request: Request, error: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"detail": error.message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_app(*, lifespan_handler=lifespan, auth_settings: AuthSettings | None = None) -> FastAPI:
    application = FastAPI(
        title="EdTech Training API",
        version="1.0.0",
        lifespan=lifespan_handler,
    )
    application.state.auth_settings = auth_settings
    origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost"
        ).split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(WorkflowError, workflow_error_handler)
    application.add_exception_handler(ConflictError, conflict_error_handler)
    application.add_exception_handler(AuthenticationError, authentication_error_handler)
    application.include_router(router)
    application.include_router(system_router)
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
