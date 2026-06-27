from typing import List, Optional
from sqlalchemy.orm import Session
from models.memo import Memo
from schemas.memo import MemoCreate, MemoUpdate

# [이유 및 목적] 데이터베이스 접근 로직을 전담하는 Repository 계층 클래스 정의
# [이점] 라우터 및 서비스 계층이 직접 SQL 쿼리나 ORM 메소드를 다루지 않게 격리하여 관심사 분리(SoC)를 실현하고 데이터 소스 변경 시 유연성을 제공함.
class MemoRepository:

    # [이유 및 목적] 메모 전체 목록 조회 및 선택적 제목 검색 기능(보너스 과제 1) 수행
    # [이점] 단일 함수로 전체 조회와 필터링 조회를 모두 지원하며, 쿼리 파라미터를 활용한 확장성을 실증함.
    @staticmethod
    def get_all(db: Session, search: Optional[str] = None) -> List[Memo]:
        query = db.query(Memo)
        if search:
            # SQLAlchemy like 쿼리 적용 (대소문자 구분 없이 부분 일치 검색)
            query = query.filter(Memo.title.like(f"%{search}%"))
        # 최신 글이 위로 오도록 내림차순 정렬
        return query.order_by(Memo.id.desc()).all()

    # [이유 및 목적] 특정 ID를 가진 단건 메모 상세 조회
    # [이점] 기본키(PK)를 활용한 빠른 단건 조회 및 데이터 존재 여부 판단 기준 제공
    @staticmethod
    def get_by_id(db: Session, memo_id: int) -> Optional[Memo]:
        return db.query(Memo).filter(Memo.id == memo_id).first()

    # [이유 및 목적] 새로운 메모 데이터를 데이터베이스에 삽입하고 세션 커밋
    # [이점] DTO(MemoCreate)를 ORM 모델로 변환하여 안전하게 DB에 영속화(Persistence)하며, refresh를 통해 생성된 ID와 날짜시간을 즉시 반영함.
    @staticmethod
    def create(db: Session, memo_data: MemoCreate) -> Memo:
        db_memo = Memo(title=memo_data.title, content=memo_data.content)
        db.add(db_memo)
        db.commit()
        db.refresh(db_memo)
        return db_memo

    # [이유 및 목적] 기존 메모 데이터를 수정하고 세션 커밋
    # [이점] 기존 데이터를 먼저 확인한 후 변경 사항만 안전하게 갱신하며, onupdate 트리거를 통해 updated_at이 자동 반영됨.
    @staticmethod
    def update(db: Session, memo_id: int, memo_data: MemoUpdate) -> Optional[Memo]:
        db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
        if db_memo:
            db_memo.title = memo_data.title
            db_memo.content = memo_data.content
            db.commit()
            db.refresh(db_memo)
            return db_memo
        return None

    # [이유 및 목적] 특정 ID의 메모를 데이터베이스에서 삭제하고 세션 커밋
    # [이점] 명확한 트랜잭션 관리 하에 영구 삭제 처리를 완료하고, 성공 여부를 boolean으로 반환하여 상위 계층의 흐름 제어를 도움.
    @staticmethod
    def delete(db: Session, memo_id: int) -> bool:
        db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
        if db_memo:
            db.delete(db_memo)
            db.commit()
            return True
        return False
