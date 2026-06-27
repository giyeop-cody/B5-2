from fastapi import FastAPI
from database import engine, Base
# ORM 모델이 메타데이터에 등록되도록 명시적 임포트
import models.memo
from routers import memo_router

# [이유 및 목적] DB 테이블 자동 생성 (Base에 등록된 모든 모델 테이블을 database.db에 생성)
# [이점] 애플리케이션 실행 시 테이블 존재 여부를 확인하고 없으면 자동 생성하므로 별도의 마이그레이션 작업 없이 즉시 실행 가능함.
Base.metadata.create_all(bind=engine)

# [이유 및 목적] FastAPI 애플리케이션 인스턴스 생성
# [이점] API 문서(Docs) 및 메인 앱 구조를 명확히 초기화하여 안정적인 웹 서비스 인프라를 구축함.
app = FastAPI(
    title="나의 메모 앱 (FastAPI CRUD Web Service)",
    description="FastAPI 기반 단일 도메인(Memo) CRUD 및 PRG 패턴 적용 웹 서비스",
    version="1.0.0"
)

# [이유 및 목적] 라우터 계층 등록 (memo_router 내의 경로들을 app에 포함)
# [이점] 메인 파일에 모든 라우터 코드를 넣지 않고 모듈화하여 관심사 분리 및 유지보수성을 극대화함.
app.include_router(memo_router.router)
