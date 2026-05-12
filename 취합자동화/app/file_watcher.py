import time
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Event
from app.excel_parser import parse_excel_file, get_existing_filenames
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import WATCH_FOLDER

# 현재 감시 중인 event_id (None이면 감시 중지)
_current_event_id: int | None = None
_observer: Observer | None = None
_lock = threading.Lock()

# 처리 대기 쿨다운 (파일 복사 완료 대기)
PROCESS_DELAY = 3  # seconds


def set_active_event(event_id: int | None):
    global _current_event_id
    with _lock:
        _current_event_id = event_id


def get_active_event_id() -> int | None:
    with _lock:
        return _current_event_id


class ExcelFileHandler(FileSystemEventHandler):
    def __init__(self):
        self._pending = {}  # filepath -> timer

    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        if self._is_excel(filepath):
            self._schedule_process(filepath)

    def on_moved(self, event):
        if event.is_directory:
            return
        filepath = event.dest_path
        if self._is_excel(filepath):
            self._schedule_process(filepath)

    def _is_excel(self, path: str) -> bool:
        _, ext = os.path.splitext(path)
        return ext.lower() in (".xlsx", ".xls", ".xlsm")

    def _schedule_process(self, filepath: str):
        # 기존 타이머 취소
        if filepath in self._pending:
            self._pending[filepath].cancel()

        timer = threading.Timer(PROCESS_DELAY, self._process_file, args=[filepath])
        self._pending[filepath] = timer
        timer.start()

    def _process_file(self, filepath: str):
        self._pending.pop(filepath, None)

        event_id = get_active_event_id()
        if event_id is None:
            print(f"[FileWatcher] 활성 이벤트 없음. 파일 무시: {filepath}")
            return

        if not os.path.exists(filepath):
            return

        print(f"[FileWatcher] 처리 시작: {filepath} (event_id={event_id})")

        db: Session = SessionLocal()
        try:
            # 이미 처리된 파일인지 확인
            already = get_existing_filenames(event_id, db)
            if os.path.basename(filepath) in already:
                print(f"[FileWatcher] 이미 처리된 파일: {filepath}")
                return

            result = parse_excel_file(filepath, event_id, db)
            print(f"[FileWatcher] 결과: {result['message']}")
        except Exception as e:
            print(f"[FileWatcher] 예외 발생: {e}")
        finally:
            db.close()


def start_watcher():
    global _observer

    os.makedirs(WATCH_FOLDER, exist_ok=True)

    if _observer and _observer.is_alive():
        return

    handler = ExcelFileHandler()
    _observer = Observer()
    _observer.schedule(handler, WATCH_FOLDER, recursive=False)
    _observer.start()
    print(f"[FileWatcher] 감시 시작: {WATCH_FOLDER}")


def stop_watcher():
    global _observer
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        print("[FileWatcher] 감시 중지")


def scan_existing_files(event_id: int, db: Session) -> list:
    """
    현재 폴더에 있는 미처리 엑셀 파일 즉시 처리.
    앱 시작 시 또는 이벤트 활성화 시 호출.
    """
    results = []
    if not os.path.exists(WATCH_FOLDER):
        return results

    already = get_existing_filenames(event_id, db)

    for fname in os.listdir(WATCH_FOLDER):
        if fname in already:
            continue
        _, ext = os.path.splitext(fname)
        if ext.lower() not in (".xlsx", ".xls", ".xlsm"):
            continue
        filepath = os.path.join(WATCH_FOLDER, fname)
        result = parse_excel_file(filepath, event_id, db)
        results.append({"filename": fname, **result})

    return results
