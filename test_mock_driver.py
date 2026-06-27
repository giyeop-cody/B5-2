import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from schemas.memo import MemoCreate, MemoUpdate
from repositories.memo_repository import MemoRepository
from services.memo_service import MemoService

# [이유 및 목적] 독립된 테스트 전용 인메모리 SQLite DB 생성
# [이점] 실제 프로덕션 DB(database.db)에 영향을 주지 않고 빠르고 완벽한 격리 테스트 수행 가능
engine_test = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# 테이블 생성
Base.metadata.create_all(bind=engine_test)

def run_tests():
    db = SessionTest()
    try:
        print("=== [START] 리팩토링된 클린 아키텍처 및 Mock 드라이버 검증 테스트 시작 ===\n")

        # 의존성 조립 (Wiring)
        repo = MemoRepository(db)
        service = MemoService(repo)

        # ---------------------------------------------------------
        # [테스트 1] 인스턴스 기반 Repository 계층 CRUD 및 검색 기능 검증
        # ---------------------------------------------------------
        print("[TEST 1] 인스턴스 기반 Repository 계층 CRUD 및 검색 기능 검증...")
        # 1. 생성 (Create)
        m1_data = MemoCreate(title="첫 번째 메모", content="모의 데이터 내용 1")
        m1 = repo.create(m1_data)
        assert m1.id == 1, f"예상 ID 1, 실제 {m1.id}"
        assert m1.title == "첫 번째 메모"
        print("  ✔️ MemoRepository.create (의존성 주입 구조) 정상 동작 확인")

        m2_data = MemoCreate(title="두 번째 테스트 메모", content="모의 데이터 내용 2")
        repo.create(m2_data)

        # 2. 전체 목록 및 검색 (Get all & Search)
        all_memos = repo.get_all()
        assert len(all_memos) == 2, f"예상 개수 2, 실제 {len(all_memos)}"
        
        # '테스트' 키워드 검색 (보너스 과제 1 검증)
        search_memos = repo.get_all(search="테스트")
        assert len(search_memos) == 1
        assert search_memos[0].title == "두 번째 테스트 메모"
        print("  ✔️ MemoRepository.get_all (like 검색 필터링) 정상 동작 확인")

        # 3. 단건 조회 (Get by ID)
        single_memo = repo.get_by_id(1)
        assert single_memo is not None
        assert single_memo.id == 1
        print("  ✔️ MemoRepository.get_by_id 정상 동작 확인")

        # 4. 수정 (Update)
        update_data = MemoUpdate(title="첫 번째 메모 수정본", content="내용 수정됨")
        updated_memo = repo.update(1, update_data)
        assert updated_memo.title == "첫 번째 메모 수정본"
        print("  ✔️ MemoRepository.update 정상 동작 확인")

        # 5. 삭제 (Delete)
        del_success = repo.delete(1)
        assert del_success is True
        assert repo.get_by_id(1) is None
        print("  ✔️ MemoRepository.delete 정상 동작 확인\n")


        # ---------------------------------------------------------
        # [테스트 2] Service 계층 비즈니스 로직 및 ServiceResult 패턴 검증 (보너스 과제 2)
        # ---------------------------------------------------------
        print("[TEST 2] Service 계층 비즈니스 로직 및 ServiceResult 패턴 검증...")
        
        # 1. 빈 값 입력 예외 검증 (빈 제목) - ServiceResult.fail 검증
        res = service.create_memo(title="", content="내용은 있음")
        assert res.success is False
        assert "제목은 비어 있을 수 없습니다" in res.error
        print("  ✔️ MemoService.create_memo (빈 제목 검증 및 ServiceResult.fail 반환) 정상 동작 확인")

        # 2. 빈 값 입력 예외 검증 (빈 내용)
        res = service.create_memo(title="제목은 있음", content="   ")
        assert res.success is False
        assert "내용은 비어 있을 수 없습니다" in res.error
        print("  ✔️ MemoService.create_memo (빈 내용 검증 및 ServiceResult.fail 반환) 정상 동작 확인")

        # 3. 정상 생성 및 ServiceResult.success 검증
        res = service.create_memo(title="서비스 테스트 메모", content="성공적인 내용")
        assert res.success is True
        assert res.data.title == "서비스 테스트 메모"
        assert hasattr(res.data, "created_at")
        print("  ✔️ MemoService.create_memo (정상 ServiceResult.success 및 DTO 반환) 정상 동작 확인")

        # 4. 없는 데이터 조회 검증
        not_found = service.get_memo_by_id(9999)
        assert not_found is None
        print("  ✔️ MemoService.get_memo_by_id (존재하지 않는 ID 조회 시 None 반환) 정상 동작 확인\n")

        print("=== [SUCCESS] 모든 리팩토링 및 Mock 드라이버 검증 테스트를 성공적으로 통과했습니다! ===")

    except AssertionError as e:
        print(f"\n❌ [ERROR] 테스트 실패: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
