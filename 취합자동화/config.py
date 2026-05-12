import os

# 취합 데이터 폴더 경로 (네이버 드라이브 동기화 폴더)
WATCH_FOLDER = "C:/취합데이터"

# DB 파일 경로
DATABASE_URL = "sqlite:///./collection.db"

# 앱 설정
APP_TITLE = "취합 자동화 시스템"
APP_VERSION = "1.0.0"

# Excel 컬럼 매핑 (1행 헤더명 → DB 필드명)
EXCEL_COLUMN_MAP = {
    "employee_id": "사번",
    "name": "이름",
    "phone": "전화번호",
    "item1": "취합사항1",
    "item2": "취합사항2",
    "item3": "취합사항3",
}

# 데이터 시작 행 (1행=헤더, 2행부터 데이터)
EXCEL_DATA_START_ROW = 2

# 처리 완료 폴더 (처리된 엑셀 파일 이동)
PROCESSED_FOLDER = "C:/취합데이터/처리완료"
