from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings


settings = get_settings()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    api_v1_router,
    prefix=settings.API_PREFIX,
)


@app.get("/")
def root() -> dict:
    return {
        "message": "RelojDAE API funcionando",
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
        "empleados": f"{settings.API_PREFIX}/empleados",
    }