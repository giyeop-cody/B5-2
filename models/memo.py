from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base

# [이유 및 목적] 메모 도메인 ORM 모델 클래스 정의 (테이블명 'memos')
# [이점] SQL 쿼리를 직접 작성하지 않고도 파이썬 객체를 통해 직관적이고 타입 안전한 CRUD 작업을 수행할 수 있음.
class Memo(Base):
    __tablename__ = "memos"

    # [이유 및 목적] 고유 식별자(PK), 자동 증가 정수형
    # [이점] 각 메모 데이터를 고유하게 식별할 수 있는 불변키 제공
    id = Column(Integer, primary_key=True, index=True)

    # [이유 및 목적] 메모 제목, 빈 값 불가(nullable=False)
    # [이점] 데이터 무결성 보호 및 검색 색인(index=True)으로 검색 속도 향상
    title = Column(String(255), nullable=False, index=True)

    # [이유 및 목적] 메모 본문 내용, 빈 값 불가(nullable=False)
    # [이점] 메모 본연의 정보를 담는 핵심 텍스트 필드
    content = Column(Text, nullable=False)

    # [이유 및 목적] 생성일시, 기본값 현재 시각
    # [이점] 작성 시점 자동 기록으로 관리 편의성 증대
    created_at = Column(DateTime, default=datetime.utcnow)

    # [이유 및 목적] 수정일시, 기본값 현재 시각, 수정 시 갱신 처리
    # [이점] 마지막 변경 시점을 추적할 수 있어 데이터 히스토리 파악에 용이
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
