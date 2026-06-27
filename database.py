import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# [이유 및 목적] SQLite 데이터베이스 파일 경로 설정 (프로젝트 루트 디렉터리에 database.db 생성)
# [이점] 파일 기반 DB로 구성하여 설정 및 실행이 간편하며, 학습자가 DB 파일의 존재 및 데이터를 즉각 확인할 수 있음.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"

# [이유 및 목적] SQLAlchemy 엔진 생성 (SQLite는 단일 파일 기반이므로 멀티스레드 접근을 위해 check_same_thread=False 설정)
# [이점] FastAPI의 비동기/멀티스레드 요청 처리 환경에서 SQLite 연결 충돌 오류를 방지함.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# [이유 및 목적] DB 세션 팩토리 생성 (autocommit=False, autoflush=False 설정으로 명시적 트랜잭션 관리)
# [이점] 커밋 시점을 직접 제어하여 트랜잭션 단위의 데이터 무결성을 유지할 수 있음.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# [이유 및 목적] ORM 모델 클래스의 기본이 되는 Base 클래스 생성
# [이점] 모든 모델 클래스가 이 Base를 상속받아 자동으로 메타데이터에 등록되므로 테이블 관리가 직관적임.
Base = declarative_base()

# [이유 및 목적] FastAPI Depends 의존성 주입을 위한 DB 세션 제너레이터 함수
# [이점] 단일 HTTP 요청 주기에 맞춰 DB 세션을 주입하고, 작업 완료 후 예외 발생 여부와 무관하게 finally 블록에서 세션을 안전하게 닫아 커넥션 누수를 원천 방지함.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
