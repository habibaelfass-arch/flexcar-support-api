from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import require_auth
from api.routes import queue, analytics, settings

app = FastAPI(
    title="Flexcar Reddit Tool API",
    description="Internal API for the Reddit monitoring and approval pipeline.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(require_auth)

app.include_router(queue.router)
app.include_router(analytics.router)
app.include_router(settings.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "flexcar-reddit-tool"}


@app.get("/health")
def health():
    return {"status": "healthy"}
