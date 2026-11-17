import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.connection import initialize_database
from app.routers import auth, categories, events, notifications, registrations
from app.routers import colleges, faculty, organizations, organizer_events, participation, points

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not settings.secret_key:
        message = "SECRET_KEY is not set. Authentication requests will be unavailable."
        if settings.is_production:
            raise RuntimeError(message)
        logger.warning(message)
    initialize_database()
    yield


app = FastAPI(
    title="EcoQuest Student API",
    description=(
        "Student authentication, event discovery, registration and notifications. "
        "Eco Points and official VTU/AICTE activity points are separate; this API does not certify academic points."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(events.router)
app.include_router(registrations.router)
app.include_router(notifications.router)
app.include_router(organizations.router)
app.include_router(organizer_events.router)
app.include_router(participation.router)
app.include_router(faculty.router)
app.include_router(colleges.router)
app.include_router(points.router)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
