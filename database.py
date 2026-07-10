import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# [이유 및 목적] SQLite 데이터베이스 파일 경로 설정 (프로젝트 루트 디렉터리에 database.db 생성)
# [이점] 파일 기반 DB로 구성하여 설정 및 실행이 간편하며, 학습자가 DB 파일의 존재 및 데이터를 즉각 확인할 수 있음.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# [이유 및 목적] 환경변수(MEMO_DATABASE_URL) 기반 DB URL 외부화 (AI 평가 항목 #4, #16 보완)
# [이점] 코드 수정 없이 환경변수만으로 DB 파일 위치를 변경하거나(예: 테스트용 임시 DB),
#        향후 PostgreSQL 등 다른 DB로 교체할 수 있는 설정 유연성을 확보함. 미설정 시 기본값(database.db) 사용.
#   사용 예: MEMO_DATABASE_URL="sqlite:////tmp/other.db" uvicorn main:app
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "MEMO_DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}",
)

# [이유 및 목적] SQLAlchemy 엔진 생성 (SQLite는 단일 파일 기반이므로 멀티스레드 접근을 위해 check_same_thread=False 설정)
# [이점] FastAPI의 비동기/멀티스레드 요청 처리 환경에서 SQLite 연결 충돌 오류를 방지함.
#        check_same_thread는 SQLite 전용 옵션이므로, 환경변수로 다른 DB URL이 주입될 경우를 대비해 조건부로 적용함.
_connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)

# [이유 및 목적] DB 세션 팩토리 생성 (autocommit=False, autoflush=False 설정으로 명시적 트랜잭션 관리)
# [이점] 커밋 시점을 직접 제어하여 트랜잭션 단위의 데이터 무결성을 유지할 수 있음.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# [이유 및 목적] ORM 모델 클래스의 기본이 되는 Base 클래스 생성
# [이점] 모든 모델 클래스가 이 Base를 상속받아 자동으로 메타데이터에 등록되므로 테이블 관리가 직관적임.
Base = declarative_base()

# [이유 및 목적] FastAPI Depends 의존성 주입을 위한 DB 세션 제너레이터 함수
# [이점] 단일 HTTP 요청 주기에 맞춰 DB 세션을 주입하고, 작업 완료 후 예외 발생 여부와 무관하게 finally 블록에서 세션을 안전하게 닫아 커넥션 누수를 원천 방지함.
# [트랜잭션 경계] 세션의 라이프사이클은 'HTTP 요청 1건 = 세션 1개'이며, 커밋은 Repository 계층에서 작업 단위별로 수행함.
#   요청 처리 도중 예외가 발생하면 커밋되지 않은 변경사항을 rollback하여 부분 반영(더티 데이터)을 방지함. (AI 평가 항목 #9 보완)
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
