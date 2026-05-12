from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Event, Submission, SourceFile
from app import file_watcher

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.created_at.desc()).all()
    active_id = file_watcher.get_active_event_id()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "events": events,
        "active_event_id": active_id,
    })


@router.post("/events/create")
async def create_event(
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    event = Event(name=name, description=description, status="collecting")
    db.add(event)
    db.commit()
    db.refresh(event)
    # 새 이벤트 생성 시 자동으로 활성화
    file_watcher.set_active_event(event.id)
    return RedirectResponse(f"/events/{event.id}", status_code=303)


@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다.")

    source_files = db.query(SourceFile).filter(SourceFile.event_id == event_id).order_by(SourceFile.processed_at.desc()).all()
    total = db.query(Submission).filter(Submission.event_id == event_id).count()
    errors = db.query(Submission).filter(Submission.event_id == event_id, Submission.is_error == True).count()
    valid = db.query(Submission).filter(
        Submission.event_id == event_id,
        Submission.is_excluded == False,
        Submission.is_error == False,
    ).count()
    active_id = file_watcher.get_active_event_id()

    return templates.TemplateResponse("event_detail.html", {
        "request": request,
        "event": event,
        "source_files": source_files,
        "total": total,
        "errors": errors,
        "valid": valid,
        "active_event_id": active_id,
    })


@router.post("/events/{event_id}/activate")
async def activate_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404)
    file_watcher.set_active_event(event_id)
    return RedirectResponse(f"/events/{event_id}", status_code=303)


@router.post("/events/{event_id}/deactivate")
async def deactivate_event(event_id: int, db: Session = Depends(get_db)):
    file_watcher.set_active_event(None)
    return RedirectResponse(f"/events/{event_id}", status_code=303)


@router.post("/events/{event_id}/close")
async def close_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404)
    event.status = "closed"
    event.closed_at = datetime.now()
    db.commit()
    if file_watcher.get_active_event_id() == event_id:
        file_watcher.set_active_event(None)
    return RedirectResponse(f"/events/{event_id}", status_code=303)


@router.post("/events/{event_id}/scan")
async def scan_files(event_id: int, db: Session = Depends(get_db)):
    """폴더 내 미처리 파일 즉시 스캔"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404)
    file_watcher.set_active_event(event_id)
    results = file_watcher.scan_existing_files(event_id, db)
    return RedirectResponse(f"/events/{event_id}", status_code=303)
