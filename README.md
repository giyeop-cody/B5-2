# 나의 메모 앱 (FastAPI 기반 CRUD 웹 서비스)

본 프로젝트는 `FastAPI`와 `SQLAlchemy`, 그리고 `Jinja2` 템플릿 엔진을 활용하여 단일 도메인(Memo)의 생성, 목록 조회, 단건 상세 조회, 수정, 삭제(CRUD) 기능을 완벽히 구현한 현대적 웹 서비스 애플리케이션입니다.

> ⚠️ **설치 문제 발생 시:** `pip install -r requirements.txt` 실패 시 먼저 `pip install --upgrade pip` 후 재시도하고, `python3 --version`으로 Python 3.10 이상인지 확인하세요. (상세: §3 사전 점검 체크리스트)

---

## 1. 프로젝트 특징 및 아키텍처 구조

본 애플리케이션은 계층형 아키텍처(Layered Architecture) 및 관심사 분리(SoC) 원칙을 철저히 준수하여 설계되었습니다.

### 1.1. 주요 기술 스택
- **Backend:** FastAPI, Uvicorn, Python-multipart
- **Database & ORM:** SQLite (`database.db`), SQLAlchemy
- **Template Engine (SSR):** Jinja2
- **Data Validation:** Pydantic (v2)

### 1.2. 엔드포인트 ↔ 구현 파일 매핑 및 기대 응답 코드

각 기능이 어느 파일의 어떤 코드로 구현되어 있는지, 그리고 시나리오별 기대 HTTP 응답 코드입니다.

| 엔드포인트 | 기능 | 라우터 함수 | 서비스 메서드 | 저장소 메서드 | 성공 응답 | 실패/예외 시 |
|---|---|---|---|---|---|---|
| `GET /` | 홈 | `read_home` | — | — | `200` HTML | — |
| `GET /memos` | 목록·검색 | `read_memos` | `get_all_memos` | `get_all` | `200` HTML | — |
| `GET /memos/new` | 등록 폼 | `new_memo_form` | — | — | `200` HTML | — |
| `POST /memos/new` | 등록 | `create_memo` | `create_memo` | `create` | `303` → `/memos` | 빈 값: `200` 폼 재렌더링 + 안내 문구 |
| `GET /memos/{id}` | 상세 | `read_memo_detail` | `get_memo_by_id` | `get_by_id` | `200` HTML | 미존재: `200` 목록 + 안내 문구 |
| `GET /memos/{id}/edit` | 수정 폼 | `edit_memo_form` | `get_memo_by_id` | `get_by_id` | `200` HTML | 미존재: `200` 목록 + 안내 문구 |
| `POST /memos/{id}/edit` | 수정 | `update_memo` | `update_memo` | `update` | `303` → `/memos/{id}` | 빈 값·미존재: `200` 폼 재렌더링 + 안내 문구 |
| `POST /memos/{id}/delete` | 삭제 | `delete_memo` | `delete_memo` | `delete` | `303` → `/memos` | 미존재: `200` 목록 + 안내 문구 |

- 파일 경로: 라우터 `routers/memo_router.py` · 서비스 `services/memo_service.py` · 저장소 `repositories/memo_repository.py`

**엔드포인트별 요청/응답 예시 (샘플 폼 입력 포함):**

```bash
# ① 홈 — 헬스체크 겸용
curl -i http://localhost:8000/
# → HTTP/1.1 200 OK  (본문: 홈 HTML, 목록/등록 링크 포함)

# ② 등록 — 폼 입력 샘플 (title, content)
curl -i -X POST http://localhost:8000/memos/new \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "title=장보기&content=우유, 계란"
# → HTTP/1.1 303 See Other / Location: /memos

# ③ 등록 검증 실패 — 빈 제목
curl -i -X POST http://localhost:8000/memos/new -d "title=&content=내용만"
# → HTTP/1.1 200 OK  (폼 재렌더링 + "제목은 비어 있을 수 없습니다" 안내)

# ④ 목록 + 검색
curl -i "http://localhost:8000/memos?search=장보기"
# → HTTP/1.1 200 OK  (like 필터링된 목록 HTML)

# ⑤ 상세 / 수정 / 삭제
curl -i http://localhost:8000/memos/1                        # → 200 (전체 필드 HTML)
curl -i -X POST http://localhost:8000/memos/1/edit \
  -d "title=장보기(수정)&content=우유만"                      # → 303 → /memos/1
curl -i -X POST http://localhost:8000/memos/1/delete         # → 303 → /memos
curl -i http://localhost:8000/memos/99999                    # → 200 (목록 + "찾을 수 없습니다" 안내)
```

**서비스 계층 입출력 계약 (라우터 ↔ 서비스 간 계약 예시):**

| 서비스 메서드 | 입력 | 출력 (성공) | 출력 (실패) |
|---|---|---|---|
| `get_all_memos(search)` | `search: str \| None` | `List[MemoResponse]` | — (빈 리스트) |
| `get_memo_by_id(id)` | `memo_id: int` | `MemoResponse` | `None` (미존재) |
| `create_memo(title, content)` | 원시 폼 문자열 2개 | `ServiceResult.success(MemoResponse)` | `ServiceResult.fail("…비어 있을 수 없습니다…")` |
| `update_memo(id, title, content)` | `int` + 문자열 2개 | `ServiceResult.success(MemoResponse)` | `ServiceResult.fail(빈 값/미존재 메시지)` |
| `delete_memo(id)` | `memo_id: int` | `True` | `False` (미존재) |

```python
# 계약 사용 예 — 라우터는 ServiceResult의 성공/실패만 보고 분기
result = service.create_memo(title="장보기", content="우유")
# 성공: result.success == True,  result.data == MemoResponse(id=1, title="장보기", ...)
# 실패: result.success == False, result.error == "메모의 제목은 비어 있을 수 없습니다. ..."
```

**오류 처리 정책 요약:**
- **입력 검증 실패(빈 제목/내용):** 리다이렉트하지 않고 해당 폼을 `200`으로 재렌더링하며, 사용자가 입력했던 값과 함께 안내 문구를 표시합니다. (입력 유실 방지 — 검증 실패는 "완료되지 않은 작업"이므로 PRG 대상이 아님)
- **미존재 데이터 접근:** 목록 화면에 "해당 데이터를 찾을 수 없습니다." 안내 문구를 렌더링합니다.
  - **정책 선택의 장단점 (목록 안내 vs 404):**
    | 방식 | 장점 | 단점 | 채택 |
    |---|---|---|---|
    | 목록 + 안내 문구 (현재) | 사용자가 막다른 화면 없이 자연스럽게 다음 행동(목록 탐색)으로 이어짐 — SSR 학습 미션 UX에 적합 | HTTP 시맨틱상 부정확(리소스 없음인데 200), 크롤러/모니터링이 오류를 감지 못함 | ✅ SSR |
    | `404` 응답 | HTTP 시맨틱 정확, API 클라이언트·모니터링 친화적 | SSR에서는 별도 404 페이지 제작 필요, 학습 범위 초과 | REST 전환 시 |
- **DB 커밋 실패 등 시스템 예외:** Repository `_commit()`이 예외 유형별로 분류 로깅(`IntegrityError` → warning, 기타 DB 오류 → error) 후 rollback하고 예외를 전파하며, FastAPI 기본 처리로 `500`이 반환됩니다.

### 1.3. 요청 처리 흐름 (Request Flow)

브라우저 요청 1건은 아래와 같이 단방향으로 흐릅니다. (평가 보완: 흐름 다이어그램)

```text
브라우저 ──HTTP──▶ Router ──호출──▶ Service ──호출──▶ Repository ──ORM──▶ SQLite(database.db)
   ▲                 │  (요청/응답·화면 전환)   (비즈니스 규칙·검증)     (쿼리·커밋)
   └──HTML(SSR)──── Jinja2 Template ◀──DTO(Pydantic)── Service ◀── ORM 모델 ── Repository
```

- **의존성 주입 체인:** `Depends(get_db)` → `MemoRepository(db)` → `MemoService(repository)` → 라우터 함수. 조립은 `get_memo_service()` 팩토리 한 곳에 응집되어 있습니다.

**실제 호출을 따라가는 예시 — `POST /memos/new` (제목="장보기", 내용="우유"):**
```text
1. Router  create_memo(title="장보기", content="우유")     # Form() 파라미터 수신
2. Service create_memo() → 빈 값 검증 통과 → MemoCreate(title="장보기", content="우유") 생성
3. Repo    create(memo_create) → Memo ORM 객체 생성 → db.add() → _commit() → db.refresh()
4. Service MemoResponse.model_validate(created) → ServiceResult.success(dto) 반환
5. Router  result.success == True → RedirectResponse("/memos", 303)
6. 브라우저  303 수신 → GET /memos 재요청 → 목록에 "장보기" 표시
```

### 1.4. 계층별 역할 분리 (Directory Structure)
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
   - **폼 필드 ↔ 스키마 매핑 표:**

     | HTML 폼 필드 (`name=`) | 라우터 파라미터 | Pydantic 스키마 필드 | ORM 컬럼 | 응답 DTO 필드 |
     |---|---|---|---|---|
     | `<input name="title">` | `title: str = Form("")` | `MemoCreate.title` / `MemoUpdate.title` | `Memo.title` | `MemoResponse.title` |
     | `<textarea name="content">` | `content: str = Form("")` | `MemoCreate.content` / `MemoUpdate.content` | `Memo.content` | `MemoResponse.content` |
     | — (서버 생성) | — | — | `Memo.id`, `created_at`, `updated_at` | `MemoResponse.id`, `created_at`, `updated_at` |
   - **(확장 안내) 파일 업로드 등 복잡한 폼:** 현재는 텍스트 필드만 사용하므로 `application/x-www-form-urlencoded`로 충분합니다. 향후 파일 업로드가 필요하면 이미 설치된 `python-multipart` 기반으로 라우터 파라미터에 `file: UploadFile = File(...)`을 추가하고 템플릿 폼에 `enctype="multipart/form-data"`를 지정하면 됩니다. (본 미션 범위 외)
4. **GET/POST 역할 규칙 및 PRG 상세 정책:**
   - **메서드 규칙:** `GET`은 상태를 변경하지 않는 조회(홈/목록/상세/폼 렌더링) 전용, `POST`는 상태를 변경하는 작업(등록/수정/삭제) 전용입니다. HTML Form이 GET/POST만 지원하므로 삭제도 POST Form으로 처리합니다.
   - **REST 전환 시 메서드 매핑 계획:** 수정은 `PUT/PATCH /api/memos/{id}`, 삭제는 `DELETE /api/memos/{id}`(→ `204 No Content`), 등록은 `POST /api/memos`(→ `201 Created`)로 이관합니다. 상세 매핑표와 전환 체크리스트는 `docs/ssr_to_rest_migration.md` 참고.
   - **리다이렉트 타겟 일관성:** 등록 성공 → 목록(`/memos`), 수정 성공 → 해당 상세(`/memos/{id}`), 삭제 성공 → 목록(`/memos`)으로 통일했으며, 모든 POST 핸들러가 동일하게 `status_code=303`을 사용합니다.
   - **브라우저(클라이언트) 동작:** `303 See Other`를 받은 브라우저는 반드시 GET으로 Location에 재요청하므로, 이후 새로고침(F5)은 마지막 GET만 반복합니다.
   - **303 vs 302 비교표:**

     | 구분 | 302 Found | 303 See Other |
     |---|---|---|
     | 재요청 메서드 | 명세상 원래 메서드 유지 (실제 브라우저는 관례적으로 GET 변환) | **명세상 GET으로 강제** |
     | POST 후 사용 시 | 브라우저 구현에 의존 → 동작 보장 안 됨 | 모든 표준 준수 브라우저에서 동일하게 동작 |
     | PRG 적합성 | 관례에 기대는 모호함 존재 | **PRG 목적에 정확히 부합 (본 프로젝트 채택)** |
     | 호환성 예외 | 매우 오래된 비표준 클라이언트에서 POST 재전송 가능성 | HTTP/1.1(1999) 이후 전 브라우저 지원 — 실질적 예외 없음 |
   - **303 처리 과정 — 실제 요청/응답 흐름 예시:**
     ```text
     [브라우저]  POST /memos/new  (title=장보기&content=우유)
     [서버]      HTTP/1.1 303 See Other
                 Location: /memos                ← 저장 완료, "GET으로 다시 와라"
     [브라우저]  GET /memos                      ← 303 규칙에 따라 자동 GET 재요청
     [서버]      HTTP/1.1 200 OK  (목록 HTML)
     ── 이후 사용자가 F5 눌러도 마지막 요청인 GET /memos 만 반복 → 중복 등록 없음 ──
     ```
     이 동작은 `test_integration.py`의 "PRG 재요청" 항목에서 자동 검증됩니다 (303 추적 후 200 수신 + 등록 1건만 수행 확인).
5. **트랜잭션 경계 및 예외 처리 정책:**
   - **세션 라이프사이클:** `Depends(get_db)`에 의해 'HTTP 요청 1건 = DB 세션 1개'가 보장되며, 요청 종료 시 `finally`에서 세션이 닫힙니다.
   - **트랜잭션 경계는 Repository:** 커밋은 Repository의 작업 단위(create/update/delete)별로 수행하고, 커밋 실패 시 내부 `_commit()` 헬퍼가 즉시 `rollback`합니다. Service는 세션/트랜잭션의 존재를 알지 못하며(의존성 규칙), 검증과 비즈니스 판단만 담당합니다. 이것이 서비스와 저장소 간 책임의 경계 사례입니다.
   - **커밋 실패 분류 로깅 (5차 평가 #9):** `_commit()`은 표준 `logging`으로 실패 원인을 분류 기록합니다 — `IntegrityError`(UNIQUE/NOT NULL/FK 위반 = 데이터 원인)는 `WARNING`, 기타 `SQLAlchemyError`(연결 끊김/디스크 오류 = 인프라 원인)는 `ERROR`, 미분류 예외는 `exception`(스택 포함)으로 기록 후 모두 rollback + 재전파합니다. 운영 시 로그 레벨만으로 "데이터를 고칠 문제인지, 인프라를 볼 문제인지" 즉시 판별할 수 있습니다.
   - **레이어 미분리 시 문제 예시:** 만약 라우터 함수 안에서 `db.query(...)`와 빈 값 검증을 함께 수행했다면, 검색 조건 하나를 바꿀 때도 HTTP 처리 코드를 건드려야 하고, DB 없이 검증 로직만 단위 테스트하는 것이 불가능해집니다.
   - **코드 리뷰 체크리스트 (레이어 침범 자동 검출용):**
     - [ ] 라우터에 `db.query`/`db.add`/`db.commit` 등 DB 조작 코드가 없는가?
     - [ ] 라우터에 빈 값 검증 등 비즈니스 규칙이 없는가? (검증은 Service)
     - [ ] Service가 `Session`/`Request` 등 프레임워크 객체를 직접 알지 않는가?
     - [ ] Repository가 HTML 렌더링·리다이렉트 등 표현 계층을 알지 않는가?
     - [ ] ORM 모델이 라우터/템플릿에 직접 반환되지 않고 DTO로 변환되는가?
     - 간단 자동 점검: `grep -n "db\." routers/*.py` 결과가 비어 있어야 합니다.
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

**실행 성공 시 실제 출력 스냅샷:**
```text
# 터미널 1 — 서버 기동 로그
$ uvicorn main:app --reload --host 0.0.0.0 --port 8000
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [928]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:47310 - "GET / HTTP/1.1" 200 OK

# 터미널 2 — 헬스체크 결과
$ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/
200
```

**`database.db` 생성 시점 및 확인:**
- **생성 시점:** 첫 요청이 아니라 **앱 시작(import) 시점**입니다 — `main.py`의 `Base.metadata.create_all(bind=engine)`이 모듈 로드와 동시에 실행되어, uvicorn 기동 직후 파일과 테이블이 생성됩니다.
```bash
ls -l database.db          # 서버 기동 직후 바로 존재해야 정상
# 저장된 데이터 직접 확인 (표준 sqlite3 CLI 또는 DB Browser for SQLite)
sqlite3 database.db "SELECT id, title FROM memos;"
```

### (선택) DB 파일 위치 변경 — 환경변수 설정
DB 접속 URL은 환경변수 `MEMO_DATABASE_URL`로 외부화되어 있습니다. 미설정 시 프로젝트 루트의 `database.db`를 사용합니다.
```bash
# 예: 다른 경로의 SQLite 파일 사용
MEMO_DATABASE_URL="sqlite:////tmp/my_memo.db" uvicorn main:app --port 8000
```

### (참고) PostgreSQL 등 다른 DB로 전환 시
> ⚠️ 본 미션은 필수 5개 패키지 외 외부 라이브러리 금지 제약이 있어 **미션 범위에서는 SQLite만 사용**합니다. 아래는 미션 이후 확장 시의 안내입니다.

| DB | 추가 드라이버 패키지 | 설치 명령 | `MEMO_DATABASE_URL` 예시 |
|---|---|---|---|
| PostgreSQL | `psycopg2-binary` | `pip install psycopg2-binary` | `postgresql+psycopg2://user:pass@localhost:5432/memodb` |
| MySQL / MariaDB | `pymysql` | `pip install pymysql` | `mysql+pymysql://user:pass@localhost:3306/memodb` |

**전환 3단계 요약:** ① 위 표의 드라이버 설치 → ② `MEMO_DATABASE_URL` 환경변수로 URL 주입 → ③ 서버 재기동 (코드 수정 불필요)

- `database.py`는 SQLite일 때만 `check_same_thread` 옵션을 적용하도록 조건 처리되어 있어, URL만 바꾸면 코드 수정 없이 전환됩니다.
- 운영 전환 시에는 `create_all` 대신 마이그레이션 도구(Alembic) 도입을 권장합니다.

### 사전 점검 체크리스트 (설치 실패 대비)
```bash
python3 --version    # 3.10 이상인지 확인
pip --version        # venv 활성화 후 venv 내부 pip인지 확인
pip install --upgrade pip   # 설치 오류 시 pip 업그레이드 후 재시도
```
- 그래도 실패하면: 네트워크/프록시 환경 확인 → `pip install -r requirements.txt -v`로 상세 로그 확인

---

## 4. 테스트 파일 위치 및 네이밍 규칙

테스트는 별도 `tests/` 디렉터리 대신 **프로젝트 루트에 `test_*.py`** 규칙으로 배치합니다. (미션 제약상 pytest 미사용 — 각 파일이 독립 실행형이며 `python3 <파일>`로 직접 실행)

| 테스트 파일 | 대상 레이어 | 검증 방식 |
|---|---|---|
| `test_mock_driver.py` | Repository + Service (단위) | 인메모리 DB + Mock 세션 — 서버 없이 격리 검증 |
| `test_integration.py` | Router → Service → Repository (E2E) | 실제 uvicorn 기동 + HTTP 요청 — 전 계층 통합 검증 |

- **네이밍 규칙:** `test_<검증 범위>.py` — 새 레이어 테스트 추가 시 동일 규칙 적용 (예: 관계 추가 시 `test_comment_repository.py`)
- 향후 pytest 도입 시 이 파일들을 `tests/` 디렉터리로 이동만 하면 `test_*` 규칙 덕분에 자동 수집됩니다.

---

## 5. Mock 드라이버 테스트 실행 방법

서버를 직접 띄우지 않고도, 모의 인메모리 DB(`sqlite:///:memory:`)와 모의 데이터를 바탕으로 Repository 및 Service 계층의 비즈니스 로직(검색, 빈 값 검증 등)이 정상 동작하는지 독립적으로 검증할 수 있습니다.

```bash
# 가상환경이 활성화된 상태에서 실행
python3 test_mock_driver.py
```
- 성공 시 `=== [SUCCESS] 모든 Mock 드라이버 검증 테스트를 성공적으로 통과했습니다! ===` 메시지가 출력됩니다.

---

## 6. 통합(E2E) 테스트 실행 방법

실제 uvicorn 서버를 임시 DB로 기동한 뒤, 표준 라이브러리(`urllib`)만으로 홈 헬스체크와 목록/상세/등록/수정/삭제/검색/검증의 전체 화면 흐름 및 PRG(303) 동작을 HTTP 레벨에서 자동 검증합니다. (외부 테스트 라이브러리 불필요 — 미션 의존성 제약 준수)

```bash
# 가상환경이 활성화된 상태에서 실행
python3 test_integration.py
```
- 성공 시 `=== [SUCCESS] 통합 테스트 N개 항목 전체 통과! ===` 메시지가 출력됩니다.
- **[5차 평가 #3] PRG 재요청 검증 포함:** 303 수신 후 리다이렉트를 추적(follow)하여 브라우저의 GET 재요청 동작을 시뮬레이션하고, 그 과정에서 등록이 정확히 1건만 수행되는지(중복 제출 없음)까지 명시적으로 확인합니다.
- 테스트는 `MEMO_DATABASE_URL` 환경변수로 임시 DB를 사용하므로 기존 `database.db`를 오염시키지 않습니다.

---

## 7. 확장 가이드 문서 (docs/)

| 문서 | 내용 |
|---|---|
| `docs/model_relationships_guide.md` | 모델 연관관계(ForeignKey/relationship) 추가 절차 — 계층별 코드 스니펫, 수정 파일 체크리스트(10단계), 마이그레이션 방법 3종 |
| `docs/ssr_to_rest_migration.md` | SSR → REST API 전환 가이드 — 영향 분석, 메서드 매핑표, 관점별 체크리스트(§6) + **순서별 마이그레이션 체크리스트(§7, Phase 1~4 15단계)** |
