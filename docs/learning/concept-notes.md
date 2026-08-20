# 개념 복습 노트

이 자료는 문장을 암기하기 위한 답안이 아니라, 구현을 직접 설명할 수 있도록 핵심 개념과 코드 근거를 연결한 복습 노트다.

## 요청 한 건을 따라가기

메모 목록을 여는 요청은 `GET /memos`에서 시작한다. Router는 쿼리 파라미터와 HTTP 응답을 다루고, Service는 조회 유스케이스를 호출하며, Repository는 SQLAlchemy SELECT를 실행한다. Service가 ORM 객체를 `MemoResponse`로 바꾸면 Router가 Jinja2 템플릿에 전달하고 서버가 완성된 HTML을 반환한다.

등록은 `POST /memos/new`에서 Form 문자열을 받은 뒤 Service의 공백 검증을 거친다. `MemoCreate`가 Repository로 전달되고, Repository는 `add → commit → refresh` 순서로 저장한다. 성공한 요청은 303으로 목록에 이동한다.

## 계층별 변경 이유

- Router: URL, GET/POST, Form, TemplateResponse, RedirectResponse
- Service: 입력 규칙, 존재 여부, 유스케이스 결과, DTO 변환
- Repository: query, add, delete, commit, rollback, refresh
- Model: 테이블과 컬럼
- Template: 사용자가 보는 HTML

화면을 바꿀 때 DB 쿼리까지 수정하지 않고, 저장 방식을 바꿀 때 HTTP 코드를 건드리지 않게 하는 것이 분리의 목적이다.

## 현재 모델을 코드로 읽기

Memo는 `id`, `title`, `content`, `created_at`, `updated_at`을 가진다. `id`는 기본키, 제목과 내용은 필수 데이터, 두 시각은 생성과 변경을 추적한다. 제목의 index는 제목 검색 쿼리를 보조한다.

`query()`는 조회 문장을 구성하고 `all()`·`first()`에서 SELECT가 실행된다. `add()`는 객체를 pending 상태로 등록하고, `commit()`의 flush 단계에서 INSERT·UPDATE·DELETE가 실행된다. `refresh()`는 DB가 생성한 값을 다시 읽는다.

## HTTP와 PRG

GET은 조회에 사용하며 반복 호출이 서버 상태를 추가로 바꾸지 않아야 한다. POST는 등록·수정·삭제처럼 상태를 바꾼다. 성공한 POST 뒤에 303을 반환하면 브라우저는 Location을 GET으로 조회한다. 이후 새로고침은 GET만 반복하므로 직전 변경 요청이 중복되지 않는다.

## Form, DTO, ORM의 차이

Form 파라미터는 브라우저 입력을 받는 경계다. Pydantic DTO는 계층 사이 데이터 계약이다. SQLAlchemy Model은 DB 테이블과 영속성 상태를 표현한다. 서로 분리해야 입력 형식과 DB 구조가 강하게 결합되지 않는다.

## SSR을 다른 표현 방식으로 바꿀 때

JSON API로 확장하면 Router의 입력·출력과 Template 계층이 가장 크게 변한다. Service의 핵심 규칙과 Repository의 CRUD는 재사용할 수 있지만, JSON 계약·HTTP 상태·CORS·프론트 상태 관리와 새로운 E2E 테스트가 필요하다.

## 저장소를 확장할 때

PostgreSQL로 옮길 때는 드라이버와 URL뿐 아니라 마이그레이션, 타입, 검색 동작, 트랜잭션 차이를 확인한다. Category 같은 관계를 추가할 때는 Model의 ForeignKey/relationship, Schema의 표현, Repository의 조회 전략, Service 규칙, Router와 화면을 순서대로 검토한다.
