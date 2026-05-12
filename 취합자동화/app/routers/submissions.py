from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Submission, Event

router = APIRouter()
templates = Jinja2Templates(directory="templates")

PAGE_SIZE = 50


@router.get("/events/{event_id}/submissions", response_class=HTMLResponse)
async def list_submissions(
    request: Request,
    event_id: int,
    filter: str = "all",  # all | error | valid
    page: int = 1,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404)

    query = db.query(Submission).filter(Submission.event_id == event_id)
    if filter == "error":
        query = query.filter(Submission.is_error == True)
    elif filter == "valid":
        query = query.filter(Submission.is_error == False, Submission.is_excluded == False)

    total = query.count()
    submissions = (
        query.order_by(Submission.is_error.desc(), Submission.created_at)
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    error_count = db.query(Submission).filter(
        Submission.event_id == event_id, Submission.is_error == True
    ).count()
    unresolved = db.query(Submission).filter(
        Submission.event_id == event_id, Submission.is_error == True, Submission.is_resolved == False
    ).count()

    return templates.TemplateResponse("submissions.html", {
        "request": request,
        "event": event,
        "submissions": submissions,
        "filter": filter,
        "page": page,
        "total": total,
        "total_pages": total_pages,
        "error_count": error_count,
        "unresolved": unresolved,
    })


@router.get("/submissions/{sub_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(Submission).filter(Submission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("submission_edit.html", {"request": request, "sub": sub})


@router.post("/submissions/{sub_id}/edit")
async def edit_submission(
    sub_id: int,
    employee_id: str = Form(...),
    name: str = Form(...),
    phone: str = Form(""),
    item1: str = Form(""),
    item2: str = Form(""),
    item3: str = Form(""),
    resolve: str = Form(""),
    db: Session = Depends(get_db),
):
    sub = db.query(Submission).filter(Submission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404)

    old_eid = sub.employee_id
    sub.employee_id = employee_id.strip()
    sub.name = name.strip()
    sub.phone = phone.strip() or None
    sub.item1 = item1.strip() or None
    sub.item2 = item2.strip() or None
    sub.item3 = item3.strip() or None

    # 사번 변경 시 중복 재검사
    if old_eid != sub.employee_id:
        conflict = db.query(Submission).filter(
            Submission.event_id == sub.event_id,
            Submission.employee_id == sub.employee_id,
            Submission.id != sub.id,
            Submission.is_excluded == False,
        ).first()
        if conflict:
            sub.is_duplicate = True
            sub.is_error = True
            sub.error_reason = f"수정 후에도 사번 중복: {sub.employee_id}"
            sub.is_resolved = False
        else:
            sub.is_duplicate = False
            sub.is_error = False
            sub.error_reason = None
            sub.is_excluded = False
            sub.is_resolved = True
    elif resolve == "yes":
        sub.is_resolved = True
        sub.is_error = False
        sub.is_duplicate = False
        sub.is_excluded = False
        sub.error_reason = None

    db.commit()
    return RedirectResponse(f"/events/{sub.event_id}/submissions?filter=error", status_code=303)


@router.post("/submissions/{sub_id}/exclude")
async def exclude_submission(sub_id: int, db: Session = Depends(get_db)):
    """이 데이터를 통계에서 제외 확정"""
    sub = db.query(Submission).filter(Submission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404)
    sub.is_excluded = True
    sub.is_resolved = True
    db.commit()
    return RedirectResponse(f"/events/{sub.event_id}/submissions?filter=error", status_code=303)


@router.post("/submissions/{sub_id}/include")
async def include_submission(sub_id: int, db: Session = Depends(get_db)):
    """제외된 데이터를 통계에 다시 포함"""
    sub = db.query(Submission).filter(Submission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404)
    sub.is_excluded = False
    sub.is_error = False
    sub.is_duplicate = False
    sub.error_reason = None
    sub.is_resolved = True
    db.commit()
    return RedirectResponse(f"/events/{sub.event_id}/submissions?filter=all", status_code=303)
