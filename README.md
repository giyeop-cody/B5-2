# 나의 메모 앱 (FastAPI 기반 CRUD 웹 서비스)

본 프로젝트는 `FastAPI`와 `SQLAlchemy`, 그리고 `Jinja2` 템플릿 엔진을 활용하여 단일 도메인(Memo)의 생성, 목록 조회, 단건 상세 조회, 수정, 삭제(CRUD) 기능을 완벽히 구현한 현대적 웹 서비스 애플리케이션입니다.

---

## 1. 프로젝트 특징 및 아키텍처 구조

본 애플리케이션은 계층형 아키텍처(Layered Architecture) 및 관심사 분리(SoC) 원칙을 철저히 준수하여 설계되었습니다.

### 1.1. 주요 기술 스택
- **Backend:** FastAPI, Uvicorn, Python-multipart
- **Database & ORM:** SQLite (`database.db`), SQLAlchemy
- **Template Engine (SSR):** Jinja2
- **Data Validation:** Pydantic (v2)

### 1.2. 요청 처리 흐름 (Request Flow)

브라우저 요청 1건은 아래와 같이 단방향으로 흐릅니다. (평가 보완: 흐름 다이어그램)

```text
브라우저 ──HTTP──▶ Router ──호출──▶ Service ──호출──▶ Repository ──ORM──▶ SQLite(database.db)
   ▲                 │  (요청/응답·화면 전환)   (비즈니스 규칙·검증)     (쿼리·커밋)
   └──HTML(SSR)──── Jinja2 Template ◀──DTO(Pydantic)── Service ◀── ORM 모델 ── Repository
```

- **의존성 주입 체인:** `Depends(get_db)` → `MemoRepository(db)` → `MemoService(repository)` → 라우터 함수. 조립은 `get_memo_service()` 팩토리 한 곳에 응집되어 있습니다.

### 1.3. 계층별 역할 분리 (Directory Structure)
```text
fastapi_crud_project/
├── main.py                 # FastAPI 앱 인스턴스 초기화 및 테이블 자동 생성
├── database.py             # SQLite DB 연결 및 Depends(get_db) 세션 제너레이터
├── models/
│   └── memo.py             # SQLAlchemy ORM 모델 클래스 (테이블: memos)
├── schemas/
│   └── memo.py             # Pydantic 기반 데이터 교환 객체 (DTO)
├── repositories/
│   └── memo_repository.py  # 데이터베이스 직접 접근 및 쿼리 전담 (get_all/get_by_id/create/update/delete, like 검색 포함)
├── services/
│   └── memo_service.py     # 비즈니스 로직 및 입력값 유효성 검증 (create_memo/update_memo 빈 값 체크 → ServiceResult 반환)
├── routers/
│   └── memo_router.py      # HTTP 요청/응답 처리, Form 수신 및 303 PRG 리다이렉트 (get_memo_service DI 팩토리 포함)
├── templates/              # Jinja2 템플릿 파일 (SSR 렌더링)
│   ├── base.html           # 전체 공통 레이아웃 및 모던 CSS 인라인 스타일
│   ├── home.html           # GET / (앱 설명 및 링크)
│   ├── memo_list.html      # GET /memos (메모 목록 및 제목 검색 폼)
│   ├── memo_detail.html    # GET /memos/{id} (메모 상세 및 수정/삭제 UX)
│   ├── memo_form.html      # GET, POST /memos/new (작성 폼)
│   └── memo_edit.html      # GET, POST /memos/{id}/edit (수정 폼)
├── docs/
│   ├── model_relationships_guide.md  # (확장 가이드) 모델 연관관계 추가 절차
│   └── ssr_to_rest_migration.md      # (확장 가이드) SSR → REST 전환 영향 분석
├── test_mock_driver.py     # Mock DB/데이터 기반 기능 및 비즈니스 검증 드라이버
├── test_integration.py     # 실제 서버 기동 기반 E2E 통합 테스트 (헬스체크 + CRUD/PRG 흐름)
├── requirements.txt        # 의존성 패키지 명세
└── README.md               # 실행 가이드 및 프로젝트 안내서
```

---

## 2. 주요 설계 및 구현 이점 (ADR 요약)

1. **계층 분리 구조:** 라우터(요청 제어), 서비스(비즈니스 규칙), 저장소(DB 처리)를 명확히 분리하여, 향후 DB 소스나 비즈니스 규칙이 변경되어도 해당 레이어만 수정하면 되는 높은 확장성과 테스트 용이성을 제공합니다.
2. **PRG (Post-Redirect-Get) 패턴 적용:** 모든 POST 요청(등록/수정/삭제) 성공 후 `status_code=303`으로 리다이렉트하여, 브라우저 새로고침(F5) 시 양식이 중복 제출되거나 동일 데이터가 중복 생성되는 문제를 원천 차단했습니다.
3. **DTO (Pydantic Schema) 디커플링:** ORM 모델 객체를 직접 뷰나 클라이언트로 반환하지 않고 DTO로 변환하여 전달함으로써 데이터 보호 및 응답 무결성을 확보했습니다.
   - **폼 → Pydantic 변환 흐름:** 브라우저 폼 데이터는 라우터에서 `Form()` 파라미터(`title`, `content`)로 수신 → Service가 빈 값 검증 후 `MemoCreate`/`MemoUpdate`(Pydantic)로 캡슐화 → Repository가 ORM 객체로 영속화 → 응답은 `MemoResponse.model_validate()`로 다시 DTO 변환됩니다. 검증 실패 시 저장 없이 `ServiceResult.fail(에러 메시지)`가 반환되어 폼 화면에 기존 입력값과 함께 안내 문구가 재렌더링됩니다.
4. **GET/POST 역할 규칙 및 PRG 상세 정책:**
   - **메서드 규칙:** `GET`은 상태를 변경하지 않는 조회(홈/목록/상세/폼 렌더링) 전용, `POST`는 상태를 변경하는 작업(등록/수정/삭제) 전용입니다. HTML Form이 GET/POST만 지원하므로 삭제도 POST Form으로 처리합니다. (REST API 전환 시 메서드 매핑은 `docs/ssr_to_rest_migration.md` 참고)
   - **리다이렉트 타겟 일관성:** 등록 성공 → 목록(`/memos`), 수정 성공 → 해당 상세(`/memos/{id}`), 삭제 성공 → 목록(`/memos`)으로 통일했으며, 모든 POST 핸들러가 동일하게 `status_code=303`을 사용합니다.
   - **브라우저(클라이언트) 동작:** `303 See Other`를 받은 브라우저는 반드시 GET으로 Location에 재요청하므로, 이후 새로고침(F5)은 마지막 GET만 반복합니다. (모든 모던 브라우저에서 동일하게 동작하며, 302와 달리 재요청 메서드가 GET으로 강제되는 것이 303을 선택한 이유입니다.)
5. **트랜잭션 경계 및 예외 처리 정책:**
   - **세션 라이프사이클:** `Depends(get_db)`에 의해 'HTTP 요청 1건 = DB 세션 1개'가 보장되며, 요청 종료 시 `finally`에서 세션이 닫힙니다.
   - **트랜잭션 경계는 Repository:** 커밋은 Repository의 작업 단위(create/update/delete)별로 수행하고, 커밋 실패 시 내부 `_commit()` 헬퍼가 즉시 `rollback`합니다. Service는 세션/트랜잭션의 존재를 알지 못하며(의존성 규칙), 검증과 비즈니스 판단만 담당합니다. 이것이 서비스와 저장소 간 책임의 경계 사례입니다.
   - **레이어 미분리 시 문제 예시:** 만약 라우터 함수 안에서 `db.query(...)`와 빈 값 검증을 함께 수행했다면, 검색 조건 하나를 바꿀 때도 HTTP 처리 코드를 건드려야 하고, DB 없이 검증 로직만 단위 테스트하는 것이 불가능해집니다.
6. **존재하지 않는 데이터 처리 정책:** 미존재 데이터 조회/수정/삭제 시 별도 404 페이지 대신 **목록 화면에 "해당 데이터를 찾을 수 없습니다." 안내 문구를 렌더링**하는 방식을 채택했습니다. SSR 학습 미션 특성상 사용자가 자연스럽게 다음 행동(목록 탐색)으로 이어지도록 하기 위함이며, REST 전환 시에는 `404 + JSON` 응답으로 대체합니다.
7. **보너스 과제 완벽 통합:**
   - **제목 검색:** 쿼리 파라미터(`?search=`)를 활용하여 Repository에서 SQLAlchemy `like` 필터링 수행.
   - **유효성 검증:** 제목이나 내용이 비어 있을 경우 Service에서 에러 메시지를 반환하고, 작성/수정 폼에 기존 입력값과 함께 오류 안내 문구를 렌더링.
   - **UX 개선:** 상세 화면에서 자연스럽게 이어지는 수정 및 삭제 버튼(Form POST 기반) 배치.

---

## 3. 실행 방법 (Quick Start Guide)

아래 순서에 따라 Python 가상환경을 생성하고 서버를 실행할 수 있습니다. (Python 3.10 이상 권장)

### Step 1: 가상환경 생성 및 활성화
```bash
# 프로젝트 루트 디렉터리로 이동
cd fastapi_crud_project

# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (Linux / macOS)
source venv/bin/activate

# 가상환경 활성화 (Windows Command Prompt)
venv\Scripts\activate.bat

# 가상환경 활성화 (Windows PowerShell)
venv\Scripts\Activate.ps1
```

### Step 2: 의존성 패키지 설치
```bash
# requirements.txt에 명시된 필수 5개 패키지 설치
pip install -r requirements.txt
```

### Step 3: FastAPI 서버 실행
```bash
# Uvicorn을 활용하여 FastAPI 서버 실행 (포트 8000)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- 서버 기동 후 브라우저에서 `http://localhost:8000`으로 접속하여 홈 화면 및 CRUD 웹 서비스를 즉시 이용할 수 있습니다.
- 터미널 로그에서 `Application startup complete.` 메시지를 통해 정상 기동을 확인할 수 있으며, 실행과 동시에 `database.db` 파일이 자동 생성됩니다.

**한 블록 요약 (생성 → 설치 → 실행):**
```bash
python3 -m venv venv && source venv/bin/activate \
  && pip install -r requirements.txt \
  && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
> 만약 `pip install` 중 오류가 발생하면 `pip install --upgrade pip` 후 재시도하고, Python 버전이 3.10 이상인지 (`python3 --version`) 확인하세요.

**간단 헬스체크:** 서버 기동 상태는 홈 엔드포인트로 즉시 확인할 수 있습니다.
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/   # 200이면 정상
```

### (선택) DB 파일 위치 변경 — 환경변수 설정
DB 접속 URL은 환경변수 `MEMO_DATABASE_URL`로 외부화되어 있습니다. 미설정 시 프로젝트 루트의 `database.db`를 사용합니다.
```bash
# 예: 다른 경로의 SQLite 파일 사용
MEMO_DATABASE_URL="sqlite:////tmp/my_memo.db" uvicorn main:app --port 8000
```

---

## 4. Mock 드라이버 테스트 실행 방법

서버를 직접 띄우지 않고도, 모의 인메모리 DB(`sqlite:///:memory:`)와 모의 데이터를 바탕으로 Repository 및 Service 계층의 비즈니스 로직(검색, 빈 값 검증 등)이 정상 동작하는지 독립적으로 검증할 수 있습니다.

```bash
# 가상환경이 활성화된 상태에서 실행
python3 test_mock_driver.py
```
- 성공 시 `=== [SUCCESS] 모든 Mock 드라이버 검증 테스트를 성공적으로 통과했습니다! ===` 메시지가 출력됩니다.

---

## 5. 통합(E2E) 테스트 실행 방법

실제 uvicorn 서버를 임시 DB로 기동한 뒤, 표준 라이브러리(`urllib`)만으로 홈 헬스체크와 목록/상세/등록/수정/삭제/검색/검증의 전체 화면 흐름 및 PRG(303) 동작을 HTTP 레벨에서 자동 검증합니다. (외부 테스트 라이브러리 불필요 — 미션 의존성 제약 준수)

```bash
# 가상환경이 활성화된 상태에서 실행
python3 test_integration.py
```
- 성공 시 `=== [SUCCESS] 통합 테스트 N개 항목 전체 통과! ===` 메시지가 출력됩니다.
- 테스트는 `MEMO_DATABASE_URL` 환경변수로 임시 DB를 사용하므로 기존 `database.db`를 오염시키지 않습니다.

---

## 6. 확장 가이드 문서 (docs/)

| 문서 | 내용 |
|---|---|
| `docs/model_relationships_guide.md` | 모델 연관관계(ForeignKey/relationship) 추가 절차 — 어느 계층의 어떤 파일에 무엇을 추가하는지 단계별 예시 |
| `docs/ssr_to_rest_migration.md` | SSR → REST API 전환 시 영향 분석 — 템플릿 제거, 라우터 변경, 메서드 매핑표, 프론트엔드 고려사항 |
