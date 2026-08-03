from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from growixa_api import __version__
from growixa_api.audit.api import router as audit_router
from growixa_api.auth.api import router as auth_router
from growixa_api.brand.api import router as brand_router
from growixa_api.company.api import router as company_router
from growixa_api.config import get_settings
from growixa_api.contacts.api import router as contacts_router
from growixa_api.health import router as health_router
from growixa_api.integrations.api import router as integrations_router
from growixa_api.jobs.api import router as jobs_router
from growixa_api.roles.api import router as roles_router
from growixa_api.templates.api import router as templates_router
from growixa_api.users.api import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title="Growixa API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(company_router)
    app.include_router(brand_router)
    app.include_router(users_router)
    app.include_router(roles_router)
    app.include_router(jobs_router)
    app.include_router(contacts_router)
    app.include_router(audit_router)
    app.include_router(integrations_router)
    app.include_router(templates_router)
    return app
