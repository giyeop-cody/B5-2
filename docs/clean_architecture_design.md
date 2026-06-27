# 클린 아키텍처 및 디자인 패턴 설계서 (Clean Architecture & Design Patterns)

본 문서는 `re_verification_report.md`에서 진단된 구조적 개선점을 해결하고, 사용자의 핵심 요구사항인 **'단일 책임 권한', '적절한 디자인 패턴', '아키텍처 개선', 'affinity, clean architecture 실현'**을 달성하기 위한 구체적인 리팩토링 설계서입니다.

---

## 1. 아키텍처 개선 전략: Clean Architecture 실현

클린 아키텍처의 핵심은 **'의존성 규칙(Dependency Rule)'**입니다. 소스 코드 의존성은 반드시 외부 계층(프레임워크, DB, 웹 UI)에서 내부 계층(비즈니스 유스케이스, 도메인 엔티티)으로만 향해야 합니다.

```text
+-------------------------------------------------------+
|  Web Framework / Driver (FastAPI, Jinja2, SQLAlchemy) |
+---------------------------+---------------------------+
                            | (Depends)
                            v
+---------------------------+---------------------------+
|      Interface Adapters (Routers, Repositories)       |
+---------------------------+---------------------------+
                            | (Constructor Injection)
                            v
+---------------------------+---------------------------+
|        Application Use Cases (MemoService)            |
+---------------------------+---------------------------+
                            | (DTO & Result Pattern)
                            v
+---------------------------+---------------------------+
|          Domain Entities / Schemas (MemoBase)         |
+-------------------------------------------------------+
```

### 1.1. 프레임워크 의존성(SQLAlchemy Session)의 완전한 격리
- **개선 방향:** 기존에 Service 계층의 메소드들이 인자로 받던 `db: Session`을 완벽히 제거합니다.
- **이유 및 목적:** `MemoService`는 순수한 애플리케이션 비즈니스 로직(유스케이스)만을 다뤄야 하며, 데이터가 SQLite에서 오는지 메모리에서 오는지 알 필요가 없도록 격리하기 위함입니다.
- **구조적 이점:** ORM이나 데이터베이스 프레임워크가 변경되어도 Service 계층은 단 한 줄의 수정도 필요치 않게 됩니다.

---

## 2. 채택된 디자인 패턴 및 단일 책임 원칙 (SRP)

### 2.1. 의존성 주입 (Dependency Injection) 및 Repository 패턴
- **구현 방식:** 
  - `MemoRepository` 클래스의 생성자 `__init__(self, db: Session)`에서 DB 세션을 주입받도록 변경하여 정적 메소드(`@staticmethod`) 구조를 탈피합니다.
  - `MemoService` 클래스의 생성자 `__init__(self, repository: MemoRepository)`에서 Repository 인스턴스를 주입받도록 설계합니다.
- **이유 및 목적:** 각 계층이 구체적인 클래스에 강하게 결합되는 것을 막고, 실행 시점에 필요한 의존성을 주입하여 제어의 역전(IoC - Inversion of Control)을 달성하기 위함입니다.
- **구조적 이점:** 단위 테스트 시 `MemoRepository` 대신 `MockRepository`를 생성하여 `MemoService`에 주입할 수 있으므로, 완벽한 격리 테스트가 가능해집니다.

### 2.2. Result 패턴 (ServiceResult Monad 캡슐화)
- **구현 방식:** `services/result.py`에 `ServiceResult` 제네릭 캡슐화 객체를 정의합니다.
  - 성공 시: `ServiceResult.success(data=...)`
  - 실패 시: `ServiceResult.fail(error=...)`
- **이유 및 목적:** 기존 `Tuple[bool, Any]` 방식의 모호함을 제거하고, 비즈니스 로직의 성공/실패 여부와 결과 데이터(또는 에러 메시지)를 명확한 규격의 도메인 객체로 캡슐화하기 위함입니다.
- **구조적 이점:** 라우터 계층에서 `if not result.success:` 형태로 일관되고 가독성 높은 예외 흐름 제어(Flow Control)가 가능해집니다.

### 2.3. 단일 책임 원칙 (SRP - Single Responsibility Principle)
- **구현 방식:** 모든 클래스와 함수는 단 하나의 '변경의 이유'만 가지도록 역할을 명확히 쪼갭니다.
  - `MemoRepository`: 데이터베이스 I/O 및 ORM 쿼리 조작 전담.
  - `MemoService`: 도메인 유스케이스 실행 및 비즈니스 정책(빈 값 검증) 전담.
  - `MemoRouter`: HTTP 통신, 의존성 주입(`Depends`), 템플릿 렌더링, 303 Redirect 전담.
  - `schemas/memo.py`: 클라이언트-서버 간 데이터 전송 규격 및 타입 검증 전담.

### 2.4. Affinity (밀접성 및 응집도 관리)
- **개념 적용:** 서로 밀접하게 연관된 책임은 한 모듈 내에 모아 응집도(High Cohesion)를 극대화하고, 서로 다른 관심사는 계층 분리를 통해 결합도(Low Coupling)를 최소화합니다.
- **실현 방안:** FastAPI의 `Depends`를 활용하여 `get_memo_service(db: Session = Depends(get_db))` 의존성 주입 팩토리 함수를 구성함으로써, 라우터가 필요한 서비스를 주입받는 코드가 팩토리 함수 한 곳에 응집되도록 관리합니다.
