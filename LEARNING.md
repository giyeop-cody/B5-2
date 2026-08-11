# B5-2 학습 노트: FastAPI CRUD 요청이 DB와 화면을 오가는 과정

이 문서는 결과를 외우기보다, 메모 한 건이 브라우저에서 SQLite까지 이동하고 다시 HTML로 돌아오는 과정을 이해하기 위한 복습 자료다.

## 1. 핵심 그림

```text
브라우저
  → Router: URL, HTTP 메서드, Form, 화면 전환
  → Service: 입력 검증과 유스케이스 판단
  → Repository: SQLAlchemy Session과 CRUD
  → SQLite
  → Repository의 ORM 객체
  → Service의 Pydantic DTO
  → Router의 Jinja2 TemplateResponse
  → 완성된 HTML
```

각 계층은 다른 이유로 변경된다. 화면 전환은 Router, 업무 규칙은 Service, 저장 방식은 Repository가 담당하면 한 부분의 변경이 나머지 코드로 번지는 범위를 줄일 수 있다.

## 2. HTTP 메서드와 화면 흐름

- GET은 홈·목록·상세·폼처럼 서버 상태를 바꾸지 않는 화면을 조회한다.
- POST는 등록·수정·삭제처럼 서버 상태를 바꾼다.
- GET이 멱등하다는 말은 같은 요청을 반복해도 서버 상태에 추가 변화가 없어야 한다는 뜻이지, 응답 내용이 영원히 같다는 뜻은 아니다.

등록 흐름은 다음과 같다.

```python
@router.post("/memos/new")
def create_memo():
    # 저장 성공 후 브라우저가 목록을 GET으로 다시 조회하게 한다.
    return RedirectResponse(url="/memos", status_code=303)
```

303을 받은 브라우저는 Location을 GET으로 다시 요청한다. 마지막 요청이 GET이 되므로 사용자가 새로고침해도 직전 POST가 다시 제출되지 않는다. 이것이 PRG(Post-Redirect-Get) 패턴이다.

## 3. Form, Pydantic, ORM

```text
<input name="title"> / <textarea name="content">
  → title: str = Form("") / content: str = Form("")
  → Service에서 공백 검사와 strip
  → MemoCreate 또는 MemoUpdate
  → Memo ORM 객체
  → MemoResponse
```

Form은 브라우저의 문자열 입력을 받는다. Pydantic 스키마는 계층 사이에서 사용할 데이터 형태를 명시한다. SQLAlchemy 모델은 DB 테이블의 구조와 영속성 동작을 담당한다. 세 객체를 분리하면 화면 입력 규칙과 DB 컬럼을 같은 객체에 억지로 묶지 않아도 된다.

## 4. SQLAlchemy 객체의 생명주기

- `query(Memo)`는 SELECT의 모양을 구성한다. 실제 조회는 `all()`이나 `first()`에서 일어난다.
- `add()`는 새 객체를 Session의 pending 상태로 등록한다.
- `commit()`은 먼저 flush하여 INSERT·UPDATE·DELETE SQL을 실행한 뒤 트랜잭션을 확정한다.
- `refresh()`는 DB가 만든 id와 시각 값을 다시 읽어 객체에 동기화한다.
- 커밋이 실패하면 `rollback()`으로 Session을 정상 상태로 되돌린 뒤 예외를 다시 전달한다.

현재 Memo는 `id`, `title`, `content`, `created_at`, `updated_at`을 가진다. 제목과 내용은 필수이고, id는 기본키이며, 시각 필드는 생성과 변경 시점을 기록한다.

## 5. 세션과 의존성 주입

`get_db()`는 요청마다 Session을 만들고 `yield`로 주입한 뒤 `finally`에서 닫는다. Router는 `Depends(get_db)`로 받은 Session을 Repository에 전달하고, Repository를 Service에 주입한다. 이 조립 지점을 한 곳에 모으면 Service가 FastAPI Request나 SQLAlchemy Session을 직접 알 필요가 없다.

## 6. SSR과 Jinja2

SSR은 서버가 데이터를 조회하고 Jinja2 템플릿에 넣어 완성된 HTML을 반환하는 방식이다. 공통 레이아웃은 `base.html`, 기능별 화면은 홈·목록·상세·등록·수정 템플릿으로 나뉜다. 템플릿은 화면 표현에 집중하고 DB 조회나 검증 규칙을 포함하지 않는다.

## 7. 설계 선택과 트레이드오프

- 단일 CRUD에서는 Repository가 작업마다 commit하는 구조가 단순하다. 여러 저장 작업을 한 번에 묶어야 한다면 Service 또는 Unit of Work가 트랜잭션 경계를 관리하는 편이 낫다.
- 검증 실패는 redirect하지 않고 같은 폼을 다시 렌더링해 입력값과 오류 문구를 보존한다.
- 없는 데이터는 현재 목록과 안내 문구를 200으로 보여준다. 사용자 흐름은 자연스럽지만 HTTP 의미를 엄격히 적용하는 REST API라면 404가 더 적절하다.
- SQLite는 학습과 로컬 실행에 간단하다. PostgreSQL로 옮길 때는 드라이버, URL, 마이그레이션, DB별 타입과 동작을 함께 검토해야 한다.

## 8. 직접 확인할 연습

1. 메모를 등록하고 303 다음에 어떤 GET이 발생하는지 네트워크 흐름을 관찰한다.
2. `database.db`를 Python `sqlite3`로 열어 화면의 값과 DB 행을 비교한다.
3. Repository의 `commit()`을 실패시키고 rollback 이후 Session을 다시 사용할 수 있는지 확인한다.
4. Router에 쿼리를 직접 넣었을 때 테스트와 변경 범위가 어떻게 나빠지는지 현재 구조와 비교한다.
5. Category 관계나 JSON API가 필요해질 때 어느 계층이 유지되고 어느 계층이 바뀌는지 설계해 본다.

## 9. 학습 정리

- 계층 분리는 파일 수를 늘리는 목적이 아니라 변경 이유를 분리하기 위한 선택이다.
- PRG는 성공한 POST 뒤의 마지막 브라우저 요청을 GET으로 바꿔 중복 제출을 막는다.
- ORM은 SQL을 없애는 도구가 아니라 객체 상태와 SQL 실행 시점을 연결하는 도구다.
- DTO는 화면·업무 규칙·DB 구조 사이의 계약을 명확하게 한다.
- 자동화 테스트는 동작 여부뿐 아니라 설계 설명이 실제 코드와 일치하는지 확인하는 학습 도구다.
