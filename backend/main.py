import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from routers import admin, auth, chat, fees, students

logging.basicConfig(level=logging.INFO)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, description=f"{settings.DEPARTMENT}, {settings.UNIVERSITY}", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

for r in (auth.router, admin.router, students.router, fees.router, chat.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok"}
