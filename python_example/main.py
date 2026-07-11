# ruff: noqa: E402
import toml
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

load_dotenv()
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from python_example.api.api_v1.api import api_router
from python_example.core.config import settings
from python_example.db.session import SessionLocal
from python_example.logger import LOG_CONFIG

app = FastAPI(
    title=settings.LINEPULSE_SVC_PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


def is_database_online():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
    except (SQLAlchemyError, TimeoutError):
        raise HTTPException(status_code=503, detail="DB is not available.")
    return {"status": "db is available."}


def get_project_version():
    with open("pyproject.toml") as file:
        pyproject = toml.load(file)
        version = pyproject["tool"]["poetry"]["version"]
        return version


app.add_api_route("/health", is_database_online)


def get_version():
    build_number = settings.LINEPULSE_SVC_BUILD_NUMBER
    # for the commit value, it needs to have a AAD check
    commit = "TODO"
    project_version = get_project_version()
    if False:
        commit = settings.LINEPULSE_SVC_VERSION
    return {
        "code": 200,
        "response": {
            "release": project_version,
            "commit": commit,
            "build_number": build_number,
        },
    }


app.add_api_route("/version", get_version)


def main():
    host = "0.0.0.0"
    port = 9080

    uvicorn.run(app, log_config=LOG_CONFIG, host=host, port=port)


if __name__ == "__main__":
    main()
