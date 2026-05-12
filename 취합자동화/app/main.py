from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import events, submissions, statistics
from app import file_watcher
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시
    init_db()
    file_watcher.start_watcher()
    yield
    # 앱 종료 시
    file_watcher.stop_watcher()


app = FastAPI(
    title="취합 자동화 시스템",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(events.router)
app.include_router(submissions.router)
app.include_router(statistics.router)


@app.get("/health")
async def health():
    return {"status": "ok", "active_event": file_watcher.get_active_event_id()}
