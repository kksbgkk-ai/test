from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Event(Base):
    """행사/취합 이벤트"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="행사명")
    description = Column(Text, nullable=True, comment="행사 설명")
    status = Column(String(20), default="collecting", comment="collecting/closed")
    created_at = Column(DateTime, default=datetime.now)
    closed_at = Column(DateTime, nullable=True)

    submissions = relationship("Submission", back_populates="event", cascade="all, delete-orphan")
    source_files = relationship("SourceFile", back_populates="event", cascade="all, delete-orphan")


class SourceFile(Base):
    """처리된 엑셀 파일 목록"""
    __tablename__ = "source_files"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    filename = Column(String(500), nullable=False, comment="파일명")
    filepath = Column(String(1000), nullable=False, comment="원본 경로")
    processed_at = Column(DateTime, default=datetime.now)
    row_count = Column(Integer, default=0, comment="처리된 행 수")
    error_count = Column(Integer, default=0, comment="오류 행 수")
    status = Column(String(20), default="ok", comment="ok/error/processing")
    error_message = Column(Text, nullable=True)

    event = relationship("Event", back_populates="source_files")
    submissions = relationship("Submission", back_populates="source_file")


class Submission(Base):
    """임직원 신청 데이터"""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    source_file_id = Column(Integer, ForeignKey("source_files.id"), nullable=True)

    # 임직원 정보
    employee_id = Column(String(50), nullable=False, index=True, comment="사번")
    name = Column(String(100), nullable=False, comment="이름")
    phone = Column(String(50), nullable=True, comment="전화번호")

    # 취합사항 (행사별 내용)
    item1 = Column(String(500), nullable=True, comment="취합사항1")
    item2 = Column(String(500), nullable=True, comment="취합사항2")
    item3 = Column(String(500), nullable=True, comment="취합사항3")

    # 상태 관리
    is_duplicate = Column(Boolean, default=False, comment="사번 중복 여부")
    is_error = Column(Boolean, default=False, comment="오류 여부")
    error_reason = Column(Text, nullable=True, comment="오류 사유")
    is_resolved = Column(Boolean, default=False, comment="오류 해결 여부")
    is_excluded = Column(Boolean, default=False, comment="통계 제외 여부")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    event = relationship("Event", back_populates="submissions")
    source_file = relationship("SourceFile", back_populates="submissions")
