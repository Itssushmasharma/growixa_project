from fastapi import FastAPI

from growixa_api import __version__
from growixa_api.brand.api import router as brand_router
from growixa_api.company.api import router as company_router
from growixa_api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Growixa API", version=__version__)
    app.include_router(health_router)
    app.include_router(company_router)
    app.include_router(brand_router)
    return app
