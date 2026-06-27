from typing import List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from repositories.memo_repository import MemoRepository
from schemas.memo import MemoCreate, MemoUpdate, MemoResponse

# [이유 및 목적] 비즈니스 로직 및 유효성 검증을 전담하는 Service 계층 클래스 정의
# [이점] 라우터는 요청 흐름 제어만 담당하고, 서비스 계층이 비즈니스 정책(빈 값 체크, DTO 변환 등)을 총괄하여 높은 모듈화 및 재사용성을 보장함.
class MemoService:

    # [이유 및 목적] 메모 목록 조회 요청을 Repository로 위임하고 결과를 DTO(MemoResponse) 리스트로 변환하여 반환
    # [이점] ORM 모델 객체를 직접 반환하지 않고 DTO로 디커플링(Decoupling)하여 보안성과 데이터 구조 무결성을 확보함.
    @staticmethod
    def get_all_memos(db: Session, search: Optional[str] = None) -> List[MemoResponse]:
        memos = MemoRepository.get_all(db, search=search)
        return [MemoResponse.model_validate(memo) for memo in memos]

    # [이유 및 목적] 특정 ID의 메모 상세 조회 요청을 처리하고 DTO로 변환하여 반환
    # [이점] 존재하지 않는 데이터일 경우 None을 반환하여 라우터가 상황에 맞는 안내 화면(예: "해당 데이터를 찾을 수 없습니다")을 처리할 수 있게 연계함.
    @staticmethod
    def get_memo_by_id(db: Session, memo_id: int) -> Optional[MemoResponse]:
        memo = MemoRepository.get_by_id(db, memo_id)
        if memo:
            return MemoResponse.model_validate(memo)
        return None

    # [이유 및 목적] 폼 기반 메모 생성 요청 시 필수값 입력 여부를 검증하고, 성공 시 저장, 실패 시 오류 메시지 반환 (보너스 과제 2)
    # [이점] 예외(Exception) 처리로 인해 서버 500 에러나 흐름 단절이 발생하지 않고, (성공 여부, 데이터 또는 에러 메시지) 형태의 유연한 결과 구조를 반환하여 템플릿에 안내 문구를 원활하게 출력할 수 있음.
    @staticmethod
    def create_memo(db: Session, title: str, content: str) -> Tuple[bool, Any]:
        if not title or title.strip() == "":
            return False, "메모의 제목은 비어 있을 수 없습니다. 제목을 입력해주세요."
        if not content or content.strip() == "":
            return False, "메모의 내용은 비어 있을 수 없습니다. 내용을 입력해주세요."
        
        memo_create = MemoCreate(title=title.strip(), content=content.strip())
        created_memo = MemoRepository.create(db, memo_create)
        return True, MemoResponse.model_validate(created_memo)

    # [이유 및 목적] 기존 메모 수정 요청 시 필수값 검증 및 존재 여부 확인 후 업데이트 처리
    # [이점] 수정 시에도 빈 값 검증 정책을 동일하게 적용하여 데이터베이스 오염을 방지하고 사용자 친화적인 피드백을 제공함.
    @staticmethod
    def update_memo(db: Session, memo_id: int, title: str, content: str) -> Tuple[bool, Any]:
        if not title or title.strip() == "":
            return False, "메모의 제목은 비어 있을 수 없습니다. 제목을 입력해주세요."
        if not content or content.strip() == "":
            return False, "메모의 내용은 비어 있을 수 없습니다. 내용을 입력해주세요."
        
        # 기존 데이터 존재 여부 확인
        existing_memo = MemoRepository.get_by_id(db, memo_id)
        if not existing_memo:
            return False, "해당 데이터를 찾을 수 없습니다."

        memo_update = MemoUpdate(title=title.strip(), content=content.strip())
        updated_memo = MemoRepository.update(db, memo_id, memo_update)
        return True, MemoResponse.model_validate(updated_memo)

    # [이유 및 목적] 특정 ID의 메모 삭제 요청을 Repository로 위임
    # [이점] 삭제 작업의 성공 여부를 반환하여 라우터가 리다이렉트나 에러 처리를 정확하게 수행할 수 있도록 지원함.
    @staticmethod
    def delete_memo(db: Session, memo_id: int) -> bool:
        return MemoRepository.delete(db, memo_id)
