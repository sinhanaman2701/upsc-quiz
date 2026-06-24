import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import documents, groups, attempts, support

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s — %(message)s")

app = FastAPI(title="UPSC Quiz API")

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(attempts.router, prefix="/api")
app.include_router(support.router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok"}
