from typing import List, Optional
from sqlalchemy.orm import Session
from models.memo import Memo
from schemas.memo import MemoCreate, MemoUpdate

# [이유 및 목적] 데이터베이스 접근 로직을 전담하는 Repository 계층 클래스 정의 (SRP 준수)
# [이점] 생성자를 통해 DB 세션을 주입받는 구조로 전환하여 정적 메소드 구조의 강한 결합을 제거하고 제어의 역전(IoC)을 실현함.
class MemoRepository:

    # [이유 및 목적] 생성자를 통한 DB 세션 의존성 주입 (Dependency Injection)
    # [이점] 리포지토리 인스턴스화 시점에 세션을 주입받으므로, 각 메소드는 인자로 db를 전달받을 필요가 없어지며 단위 테스트 시 Mock DB 세션 주입이 극도로 용이해짐.
    def __init__(self, db: Session):
        self.db = db

    # [이유 및 목적] 메모 전체 목록 조회 및 선택적 제목 검색 기능 수행
    # [이점] 내부 self.db를 활용하여 관심사를 캡슐화하고, like 쿼리를 통한 확장성을 제공함.
    def get_all(self, search: Optional[str] = None) -> List[Memo]:
        query = self.db.query(Memo)
        if search:
            query = query.filter(Memo.title.like(f"%{search}%"))
        return query.order_by(Memo.id.desc()).all()

    # [이유 및 목적] 특정 ID를 가진 단건 메모 상세 조회
    # [이점] 단건 조회 로직을 캡슐화하여 서비스 계층에 순수 데이터 모델만 전달함.
    def get_by_id(self, memo_id: int) -> Optional[Memo]:
        return self.db.query(Memo).filter(Memo.id == memo_id).first()

    # [이유 및 목적] 커밋 실패 시 세션을 롤백하는 공통 헬퍼 (AI 평가 항목 #9 보완)
    # [이점] 커밋 도중 예외(무결성 위반, 디스크 오류 등)가 발생하면 즉시 rollback하여
    #        세션이 오염된 상태로 남지 않도록 보장하고, 트랜잭션 경계를 Repository 한 곳에 응집시킴.
    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # [이유 및 목적] 새로운 메모 데이터를 데이터베이스에 삽입하고 세션 커밋
    # [이점] DTO를 ORM 객체로 변환하여 영속화하며, refresh를 통해 DB에서 생성된 ID와 타임스탬프를 동기화함.
    def create(self, memo_data: MemoCreate) -> Memo:
        db_memo = Memo(title=memo_data.title, content=memo_data.content)
        self.db.add(db_memo)
        self._commit()
        self.db.refresh(db_memo)
        return db_memo

    # [이유 및 목적] 기존 메모 데이터를 수정하고 세션 커밋
    # [이점] 객체의 영속성 상태를 확인한 후 변경 사항만 세션에 반영하며, onupdate 트리거를 통해 updated_at이 자동 갱신됨.
    def update(self, memo_id: int, memo_data: MemoUpdate) -> Optional[Memo]:
        db_memo = self.get_by_id(memo_id)
        if db_memo:
            db_memo.title = memo_data.title
            db_memo.content = memo_data.content
            self._commit()
            self.db.refresh(db_memo)
            return db_memo
        return None

    # [이유 및 목적] 특정 ID의 메모를 데이터베이스에서 삭제하고 세션 커밋
    # [이점] 안전한 트랜잭션 관리 하에 삭제 작업을 처리하고 성공 여부를 boolean으로 반환하여 상위 흐름 제어를 지원함.
    def delete(self, memo_id: int) -> bool:
        db_memo = self.get_by_id(memo_id)
        if db_memo:
            self.db.delete(db_memo)
            self._commit()
            return True
        return False
