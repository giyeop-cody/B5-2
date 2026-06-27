# 과제 해석 (Task Analysis)

본 문서는 `FastAPI 기반 CRUD 웹 서비스 구축` 미션을 수행하기 위해 미션 내용을 어떤 지식을 기반으로 어떻게 해석했는지에 대한 종합 분석 문서입니다.

---

## 1. 기반 지식 체계 (Applied Knowledge Base)

본 과제를 해석하고 설계하는 데 있어 다음과 같은 핵심 소프트웨어 공학 및 웹 프레임워크 지식 체계가 활용되었습니다.

### 1.1. 계층형 아키텍처 (Layered Architecture) 및 관심사 분리 (SoC)
- **개념:** 웹 애플리케이션의 복잡도를 낮추기 위해 요청 처리(Router/Controller), 비즈니스 로직(Service), 데이터 접근(Repository), 데이터 모델(Entity/Model)을 분리하는 설계 패턴입니다.
- **해석 기준:** FastAPI의 라우터 함수 내에 DB 쿼리나 비즈니스 검증 로직을 혼재시키지 않고, 역할별로 명확히 책임을 분할하여 유지보수성과 테스트 용이성을 확보합니다.

### 1.2. PRG (Post-Redirect-Get) 패턴
- **개념:** 웹 브라우저에서 POST 요청(등록/수정/삭제)을 보낸 후 서버가 바로 화면을 렌더링하면, 사용자가 새로고침(F5)을 누를 때 동일한 POST 요청이 중복 전송되는 문제를 방지하기 위한 웹 표준 패턴입니다.
- **해석 기준:** 모든 POST 요청 처리 함수는 작업 완료 후 `RedirectResponse`를 반환하며, HTTP 상태 코드 `303 (See Other)`을 명시하여 브라우저가 명시적으로 GET 요청을 통해 결과 화면(목록 또는 상세)으로 이동하도록 강제합니다.

### 1.3. SSR (Server-Side Rendering) 및 Jinja2 템플릿 엔진
- **개념:** 클라이언트(브라우저)에서 자바스크립트로 DOM을 생성하는 SPA(Single Page Application) 방식과 달리, 서버에서 Jinja2 템플릿 엔진을 활용해 동적으로 HTML을 렌더링하여 완성된 문서를 전달하는 방식입니다.
- **해석 기준:** FastAPI의 `Jinja2Templates` 인스턴스를 활용하여 `TemplateResponse`를 반환하며, 템플릿 파일들은 오직 `templates/` 디렉터리에 위치시킵니다.

### 1.4. SQLAlchemy ORM 및 의존성 주입 (FastAPI Depends)
- **개념:** 데이터베이스 테이블과 Python 클래스를 매핑(ORM)하여 SQL 쿼리 대신 객체 지향적으로 데이터를 다룹니다. 또한, FastAPI의 `Depends` 메커니즘을 통해 HTTP 요청 주기에 맞춰 DB 세션을 생성하고 종료하는 라이프사이클 관리를 수행합니다.
- **해석 기준:** `database.py`에서 `get_db()` 제너레이터를 구현하여 `yield` 방식으로 세션을 제공하고, 예외 발생 여부와 무관하게 `finally` 블록에서 세션을 안전하게 닫도록 설계합니다.

### 1.5. DTO (Data Transfer Object) / Pydantic 스키마 패턴
- **개념:** ORM 모델 객체를 직접 외부 뷰(View)나 클라이언트에 노출하지 않고, 전송 전용 스키마(Pydantic Model)를 통해 데이터 구조와 타입 유효성을 검증하는 패턴입니다.
- **해석 기준:** 권장 사항에 따라 `schemas/` 디렉터리를 별도 구성하여 Form 파라미터나 뷰 렌더링에 필요한 데이터를 캡슐화합니다.

---

## 2. 세부 요구사항별 해석 및 도메인 선정

### 2.1. 도메인 선정: '메모 관리 (Memo)'
- **도메인 정의:** 사용자가 일상적인 메모를 작성하고 관리하는 시스템.
- **필드 구성 (3~6개 권장 제약 충족):**
  1. `id` (정수, 기본키, 자동 증가)
  2. `title` (문자열, 메모 제목, 필수값)
  3. `content` (문자열, 메모 본문, 필수값)
  4. `created_at` (날짜시간, 생성일시, 기본값 `now()`)
  5. `updated_at` (날짜시간, 수정일시, 기본값 `now()`, 수정 시 갱신)

### 2.2. 폼 기반 입력 및 파라미터 수신 해석
- HTML Form의 `enctype="application/x-www-form-urlencoded"` 요청을 처리하기 위해 FastAPI의 `Form(...)` 의존성을 라우터 파라미터에 명시합니다.
- 수신된 Form 데이터는 Service 계층으로 전달되기 전 또는 Service 계층 내에서 Pydantic 스키마나 비즈니스 객체로 검증됩니다.

### 2.3. 보너스 과제 (선택 사항) 통합 해석
- **검색 기능:** `GET /memos` (또는 `GET /`) 요청 시 선택적 쿼리 파라미터 `search: Optional[str]`을 수신하여 Repository에서 SQLAlchemy `filter(Memo.title.like(f"%{search}%"))`를 실행하도록 구현합니다.
- **검증 처리:** 제목(`title`)이나 내용(`content`)이 빈 문자열일 경우, Service 계층에서 예외를 발생시키거나 검증 오류 메시지를 반환하여 작성/수정 폼 템플릿에 에러 문구가 함께 렌더링되도록 처리합니다.
- **UX 개선:** 상세 화면(`memo_detail.html`)에서 수정 및 삭제 버튼을 적절히 배치하고, 삭제의 경우 HTML Form(`POST` 방식으로 동작하되 액션을 명확히 구분)을 사용하여 자연스러운 흐름을 설계합니다.
