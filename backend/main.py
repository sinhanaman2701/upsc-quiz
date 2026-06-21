from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import documents, groups, attempts

app = FastAPI(title="UPSC Quiz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(attempts.router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok"}
