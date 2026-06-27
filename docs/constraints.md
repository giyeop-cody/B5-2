# 개발 환경 및 제약 사항 (Constraints)

## 1. 개발 환경
- **Python:** 3.10 이상

---

## 2. 제약 사항

### 2.1. 의존성 (Dependencies)
- `fastapi`, `uvicorn`, `sqlalchemy`, `jinja2`, `python-multipart` 범위 내에서만 사용한다.
- 그 외 외부 라이브러리는 추가하지 않는다.

### 2.2. 프로젝트 구조 (Structure)
- 라우터, 서비스, 저장소, 모델 코드는 역할에 맞게 분리한다.
- 템플릿 파일은 `templates/` 디렉터리 아래에 둔다.

### 2.3. 기능 범위 (Scope Limitation)
- **로그인 / 권한 / 인증은 구현하지 않는다.** (이 내용은 다음 미션에서 다룬다.)
- **모델 간 관계 (연관관계)는 구현하지 않는다.** (이 내용도 다음 미션에서 다룬다.)

### 2.4. 권장 사항 (Recommendations)
- SQLAlchemy ORM 모델을 직접 라우터에서 반환하지 않고, **Pydantic Schema (요청/응답 모델) 또는 별도 DTO 객체로 분리하여 사용하는 것을 권장**한다.
