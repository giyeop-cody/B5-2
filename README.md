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

### 1.2. 계층별 역할 분리 (Directory Structure)
```text
fastapi_crud_project/
├── main.py                 # FastAPI 앱 인스턴스 초기화 및 테이블 자동 생성
├── database.py             # SQLite DB 연결 및 Depends(get_db) 세션 제너레이터
├── models/
│   └── memo.py             # SQLAlchemy ORM 모델 클래스 (테이블: memos)
├── schemas/
│   └── memo.py             # Pydantic 기반 데이터 교환 객체 (DTO)
├── repositories/
│   └── memo_repository.py  # 데이터베이스 직접 접근 및 쿼리 전담 (like 검색 포함)
├── services/
│   └── memo_service.py     # 비즈니스 로직 및 입력값 유효성 검증 (빈 값 체크)
├── routers/
│   └── memo_router.py      # HTTP 요청/응답 처리, Form 수신 및 303 PRG 리다이렉트
├── templates/              # Jinja2 템플릿 파일 (SSR 렌더링)
│   ├── base.html           # 전체 공통 레이아웃 및 모던 CSS 인라인 스타일
│   ├── home.html           # GET / (앱 설명 및 링크)
│   ├── memo_list.html      # GET /memos (메모 목록 및 제목 검색 폼)
│   ├── memo_detail.html    # GET /memos/{id} (메모 상세 및 수정/삭제 UX)
│   ├── memo_form.html      # GET, POST /memos/new (작성 폼)
│   └── memo_edit.html      # GET, POST /memos/{id}/edit (수정 폼)
├── test_mock_driver.py     # Mock DB/데이터 기반 기능 및 비즈니스 검증 드라이버
├── requirements.txt        # 의존성 패키지 명세
└── README.md               # 실행 가이드 및 프로젝트 안내서
```

---

## 2. 주요 설계 및 구현 이점 (ADR 요약)

1. **계층 분리 구조:** 라우터(요청 제어), 서비스(비즈니스 규칙), 저장소(DB 처리)를 명확히 분리하여, 향후 DB 소스나 비즈니스 규칙이 변경되어도 해당 레이어만 수정하면 되는 높은 확장성과 테스트 용이성을 제공합니다.
2. **PRG (Post-Redirect-Get) 패턴 적용:** 모든 POST 요청(등록/수정/삭제) 성공 후 `status_code=303`으로 리다이렉트하여, 브라우저 새로고침(F5) 시 양식이 중복 제출되거나 동일 데이터가 중복 생성되는 문제를 원천 차단했습니다.
3. **DTO (Pydantic Schema) 디커플링:** ORM 모델 객체를 직접 뷰나 클라이언트로 반환하지 않고 DTO로 변환하여 전달함으로써 데이터 보호 및 응답 무결성을 확보했습니다.
4. **보너스 과제 완벽 통합:**
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

---

## 4. Mock 드라이버 테스트 실행 방법

서버를 직접 띄우지 않고도, 모의 인메모리 DB(`sqlite:///:memory:`)와 모의 데이터를 바탕으로 Repository 및 Service 계층의 비즈니스 로직(검색, 빈 값 검증 등)이 정상 동작하는지 독립적으로 검증할 수 있습니다.

```bash
# 가상환경이 활성화된 상태에서 실행
python3 test_mock_driver.py
```
- 성공 시 `=== [SUCCESS] 모든 Mock 드라이버 검증 테스트를 성공적으로 통과했습니다! ===` 메시지가 출력됩니다.
