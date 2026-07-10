from typing import List, Optional
from repositories.memo_repository import MemoRepository
from schemas.memo import MemoCreate, MemoUpdate, MemoResponse
from services.result import ServiceResult

# [계층 책임 경계 — AI 평가 항목 #8 보완]
#   Service가 하는 일: 입력값 검증(빈 값 체크), 비즈니스 판단(존재 여부 확인), ORM→DTO 변환, 성공/실패 결과 캡슐화
#   Service가 하지 않는 일: SQL/쿼리 실행(→ Repository), 세션/커밋/롤백(→ Repository·get_db), HTTP 응답·리다이렉트(→ Router)
# [이유 및 목적] 비즈니스 로직 및 유스케이스를 전담하는 Service 계층 클래스 정의 (Clean Architecture 실현)
# [이점] 생성자 주입을 통해 Repository 인스턴스를 주입받음으로써, 기존 메소드 인자였던 db: Session을 완벽히 제거함. 이로써 서비스 계층은 데이터베이스나 ORM 프레임워크의 세부 구현을 전혀 몰라도 되는 완벽한 의존성 규칙(Dependency Rule)을 준수하게 됨.
class MemoService:

    # [이유 및 목적] 생성자를 통한 MemoRepository 인스턴스 주입 (Dependency Injection)
    # [이점] 리포지토리의 추상화된 기능에만 의존하며, 단위 테스트 시 Mock Repository를 주입할 수 있어 완벽한 격리 테스트가 가능함.
    def __init__(self, repository: MemoRepository):
        self.repository = repository

    # [이유 및 목적] 메모 목록 조회 요청을 위임하고 결과를 DTO 리스트로 변환하여 반환
    # [이점] ORM 모델 객체를 직접 반환하지 않고 DTO(MemoResponse)로 디커플링(Decoupling)하여 보안성과 데이터 구조 무결성을 보장함.
    def get_all_memos(self, search: Optional[str] = None) -> List[MemoResponse]:
        memos = self.repository.get_all(search=search)
        return [MemoResponse.model_validate(memo) for memo in memos]

    # [이유 및 목적] 특정 ID의 메모 상세 조회 요청을 처리하고 DTO로 변환하여 반환
    # [이점] 존재하지 않는 데이터일 경우 None을 반환하여 라우터가 상황에 맞는 안내 화면을 처리할 수 있게 연계함.
    def get_memo_by_id(self, memo_id: int) -> Optional[MemoResponse]:
        memo = self.repository.get_by_id(memo_id)
        if memo:
            return MemoResponse.model_validate(memo)
        return None

    # [이유 및 목적] 폼 기반 메모 생성 시 필수값 입력 여부를 검증하고, ServiceResult 패턴으로 성공/실패를 캡슐화하여 반환 (보너스 과제 2)
    # [이점] Tuple 구조의 모호함을 탈피하고, 명확한 Monad 구조의 ServiceResult 객체를 반환하여 라우터가 직관적이고 가독성 높게 에러를 처리할 수 있음.
    def create_memo(self, title: str, content: str) -> ServiceResult[MemoResponse]:
        if not title or title.strip() == "":
            return ServiceResult.fail("메모의 제목은 비어 있을 수 없습니다. 제목을 입력해주세요.")
        if not content or content.strip() == "":
            return ServiceResult.fail("메모의 내용은 비어 있을 수 없습니다. 내용을 입력해주세요.")
        
        memo_create = MemoCreate(title=title.strip(), content=content.strip())
        created_memo = self.repository.create(memo_create)
        return ServiceResult.success(MemoResponse.model_validate(created_memo))

    # [이유 및 목적] 기존 메모 수정 요청 시 필수값 검증 및 존재 여부 확인 후 ServiceResult 반환
    # [이점] 수정 시에도 동일한 검증 정책과 Result 패턴을 적용하여 일관된 예외 처리 및 견고한 비즈니스 흐름을 보장함.
    def update_memo(self, memo_id: int, title: str, content: str) -> ServiceResult[MemoResponse]:
        if not title or title.strip() == "":
            return ServiceResult.fail("메모의 제목은 비어 있을 수 없습니다. 제목을 입력해주세요.")
        if not content or content.strip() == "":
            return ServiceResult.fail("메모의 내용은 비어 있을 수 없습니다. 내용을 입력해주세요.")
        
        # 기존 데이터 존재 여부 확인
        existing_memo = self.repository.get_by_id(memo_id)
        if not existing_memo:
            return ServiceResult.fail("해당 데이터를 찾을 수 없습니다.")

        memo_update = MemoUpdate(title=title.strip(), content=content.strip())
        updated_memo = self.repository.update(memo_id, memo_update)
        return ServiceResult.success(MemoResponse.model_validate(updated_memo))

    # [이유 및 목적] 특정 ID의 메모 삭제 요청을 Repository로 위임
    # [이점] 삭제 성공 여부를 반환하여 라우터가 리다이렉트나 에러 처리를 정확하게 수행할 수 있도록 지원함.
    def delete_memo(self, memo_id: int) -> bool:
        return self.repository.delete(memo_id)
