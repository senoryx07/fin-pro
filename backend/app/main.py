from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.company import router as company_router
from backend.app.api.market import router as market_router
from backend.app.api.security import router as security_router
from backend.app.database.database import create_db_and_tables
from backend.app.database.seed import seed_companies
from backend.app.models.market_data import DailyPrice

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_companies()

    yield


app = FastAPI(
    title="Fin Pro API",
    description="Financial Research & Analytics Platform",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(company_router)
app.include_router(market_router)
app.include_router(security_router)


@app.get("/")
def root():
    return {
        "application": "Fin Pro",
        "message": "Financial Research & Analytics Platform",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Fin Pro Backend",
    }