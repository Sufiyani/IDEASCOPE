"""
IdeaScope – FastAPI application entry point.
Owner: Member 2 (Sufiyaan Imran)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, groups, health, jobs, users

app = FastAPI(title="IdeaScope API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
app.include_router(groups.router, prefix="/groups")
app.include_router(jobs.router, prefix="/jobs")

# Member 3 routers: add include_router lines here

# Member 1 routers: add include_router lines here
