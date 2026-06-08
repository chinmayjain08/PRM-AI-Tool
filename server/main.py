from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import auth_router, admin_router, manager_router, employee_router
from app.core.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs startup tasks before the server starts accepting requests."""
    start_scheduler()
    yield


app = FastAPI(
    title       = "PRM Tool API",
    description = "Project & Resource Management Tool — Learn & Code Final Project",
    lifespan    = lifespan,
)

app.include_router(auth_router.router,     prefix="/auth",     tags=["Auth"])
app.include_router(admin_router.router,    prefix="/admin",    tags=["Admin"])
app.include_router(manager_router.router,  prefix="/manager",  tags=["Manager"])
app.include_router(employee_router.router, prefix="/employee", tags=["Employee"])
