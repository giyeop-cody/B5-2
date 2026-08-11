# 구현 관찰 실습

설명을 외우기 전에 아래 실습을 수행하고, 관찰한 사실을 자신의 말로 기록한다.

## 실습 1. 브라우저와 서버 로그 연결

서버를 실행한 뒤 홈, 목록, 등록 폼을 차례로 연다. 주소·HTTP 메서드·상태 코드·서버 로그를 한 줄씩 기록한다. 홈과 목록 중 어느 요청이 DB를 사용하는지도 코드에서 확인한다.

## 실습 2. 등록 요청 추적

메모 한 건을 등록하면서 다음 파일에 도달하는 순서를 따라간다.

```text
routers/memo_router.py
services/memo_service.py
repositories/memo_repository.py
models/memo.py
schemas/memo.py
templates/memo_list.html
```

각 파일에서 입력값의 타입과 반환값의 타입을 메모한다.

## 실습 3. PRG 관찰

리다이렉트를 자동으로 따르지 않는 HTTP 요청으로 등록을 보내 303과 Location을 확인한다. 그다음 리다이렉트를 따라가 최종 요청이 GET인지 확인한다. 등록 전후 DB 행 수를 비교해 한 건만 늘어났는지 확인한다.

## 실습 4. DB 직접 읽기

```python
import sqlite3

con = sqlite3.connect("database.db")
for row in con.execute(
    "SELECT id, title, content, created_at, updated_at FROM memos ORDER BY id"
):
    print(row)
```

화면의 상세 정보와 DB 행이 일치하는지 비교한다.

## 실습 5. 실패 경로 보기

빈 제목과 빈 내용을 각각 제출하고 저장되지 않는지 확인한다. 존재하지 않는 id의 상세·수정·삭제 흐름도 관찰한다. 검증 실패와 시스템 예외가 왜 다른 방식으로 처리되어야 하는지 적어 본다.

## 실습 6. 책임 이동 실험

Repository의 query를 Router로 옮긴 가상 코드를 짧게 작성한다. DB 없이 Service 규칙만 확인하려 할 때 무엇이 어려워지는지, 같은 검증이 여러 라우트에 생기면 어떤 문제가 생기는지 비교한다.

## 실습 7. 다음 변화 설계

코드를 바로 수정하지 말고 다음 두 변화의 영향 범위를 표로 그린다.

- Memo에 Category 관계 추가
- Jinja2 화면을 별도 프론트엔드와 JSON API로 분리

유지되는 계층, 바뀌는 계층, 새로 필요한 테스트를 나눠 기록한다.
