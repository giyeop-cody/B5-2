# 프로젝트 구현 계획 (Project Plan)

본 문서는 `과제 해석` 및 `해석 내용 검증`을 바탕으로, 책임과 기능으로 나누어 큰 틀부터 작은 틀, 세부 구현 순으로 진행하기 위한 체계적인 Top-down 개발 로드맵입니다.

---

## 1. Git 브랜치 전략 및 워크플로우

- **`evel` 브랜치:** 과제 진행 도중에 나온 중간 산출물(기획/설계 문서, 아키텍처 결정 기록 등)을 평가받고 모아두는 중심 브랜치입니다.
- **`test` 브랜치:** 실제 소스 코드 구현 및 Mock 드라이버/Mock 데이터를 활용한 기능 검증 및 테스트를 수행하는 브랜치입니다.
- **`master` 브랜치:** 모든 구현과 검증이 완료된 최종 완성본을 병합하여 제출하는 브랜치입니다.

---

## 2. 단계별 Top-down 구현 로드맵

### Phase 1: 큰 틀 (프로젝트 뼈대 및 인프라) 구축
1. **패키지 명세 생성 (`requirements.txt`)**
   - 필수 패키지 5개(`fastapi`, `uvicorn`, `sqlalchemy`, `jinja2`, `python-multipart`) 명시.
2. **계층별 디렉터리 뼈대 생성**
   - `models/`, `schemas/`, `repositories/`, `services/`, `routers/`, `templates/` 디렉터리 구성.
3. **데이터베이스 연결 인프라 (`database.py`)**
   - SQLite DB(`database.db`) 파일 기반 엔진 생성.
   - `sessionmaker` 설정 및 의존성 주입을 위한 `get_db()` 제너레이터 함수 구현.
4. **애플리케이션 진입점 (`main.py`)**
   - FastAPI 애플리케이션 인스턴스 초기화 및 DB 테이블 자동 생성(`Base.metadata.create_all`).
   - 기본 라우터 등록 및 템플릿 미들웨어 뼈대 설정.

### Phase 2: 데이터 모델 및 DTO 스키마 구현
1. **ORM 도메인 모델 (`models/memo.py`)**
   - `Memo` 클래스 정의 (테이블명: `memos`).
   - 컬럼: `id`(Integer, PK), `title`(String, Non-nullable), `content`(Text, Non-nullable), `created_at`(DateTime), `updated_at`(DateTime).
2. **DTO 스키마 (`schemas/memo.py`)**
   - Pydantic 모델 정의: `MemoCreate`, `MemoUpdate`, `MemoResponse`.
   - ORM 모드(`from_attributes=True`) 활성화.

### Phase 3: 계층별 책임 및 비즈니스 로직 구현 (Repositories & Services)
1. **저장소 계층 (`repositories/memo_repository.py`)**
   - `MemoRepository` 클래스 구현.
   - `get_all(db, search)`: 전체 목록 조회 및 제목 기준 `like` 검색 기능 (보너스 과제 1).
   - `get_by_id(db, memo_id)`: 단건 상세 조회.
   - `create(db, memo)`: 메모 삽입.
   - `update(db, memo_id, memo_update)`: 메모 내용 및 `updated_at` 갱신.
   - `delete(db, memo_id)`: 메모 삭제.
2. **서비스 계층 (`services/memo_service.py`)**
   - `MemoService` 클래스 구현.
   - 비즈니스 검증 로직: 제목이나 내용이 비어 있을 경우 에러 핸들링 또는 템플릿용 에러 메시지 생성 (보너스 과제 2).
   - 없는 데이터 조회 시 `None` 반환 또는 예외 발생을 통해 라우터가 안내 화면으로 처리할 수 있도록 연계.

### Phase 4: 라우터 및 SSR 템플릿 구현 (Routers & Templates)
1. **라우터 계층 (`routers/memo_router.py`)**
   - `APIRouter` 인스턴스 생성 및 `main.py`에 등록.
   - `GET /`: 홈 화면 렌더링 (`home.html`).
   - `GET /memos`: 메모 목록 화면 렌더링 (`memo_list.html`, 검색 파라미터 지원).
   - `GET /memos/new`: 새 메모 작성 폼 렌더링 (`memo_form.html`).
   - `POST /memos/new`: `Form()` 데이터 수신, 생성 후 `RedirectResponse(url='/memos', status_code=303)`.
   - `GET /memos/{memo_id}`: 단건 상세 화면 렌더링 (`memo_detail.html`, 없는 ID일 시 에러 안내 처리).
   - `GET /memos/{memo_id}/edit`: 수정 폼 렌더링 (`memo_edit.html`).
   - `POST /memos/{memo_id}/edit`: 수정 처리 후 `RedirectResponse(url='/memos/{memo_id}', status_code=303)`.
   - `POST /memos/{memo_id}/delete`: 삭제 처리 후 `RedirectResponse(url='/memos', status_code=303)`.
2. **Jinja2 템플릿 (`templates/`)**
   - `base.html`: 레이아웃 뼈대 및 기본 네비게이션.
   - `home.html`, `memo_list.html`, `memo_detail.html`, `memo_form.html`, `memo_edit.html`.
   - 자연스러운 수정/삭제 버튼 및 네비게이션 UX 설계 (보너스 과제 3).

### Phase 5: Mock 드라이버 및 Mock 데이터 검증
1. **테스트 스크립트 (`test_mock_driver.py`)**
   - 실제 서버 기동 전/후, Repository와 Service 계층이 정상 동작하는지 Mock DB 세션 및 Mock 데이터를 통해 독립적으로 실행하고 검증하는 드라이버 작성.
   - `test` 브랜치에서 실행하여 동작 무결성을 확인하고 결과를 기록함.

### Phase 6: 최종 통합 및 제출물 구성
1. **README.md 작성**
   - 가상환경 생성, 패키지 설치, 서버 실행 순서 등 상세 가이드 수록.
2. **브랜치 병합**
   - `test` 브랜치에서 모든 검증 통과 후 `master` 브랜치로 병합.
