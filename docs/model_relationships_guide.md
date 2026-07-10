# 모델 연관관계(Relationship) 추가 가이드

> **주의:** 본 미션의 제약 사항에 따라 모델 간 연관관계는 **구현하지 않았습니다** (다음 미션 범위).
> 본 문서는 AI 사전평가 보완 요구(평가 항목 #17)에 따라, **향후 연관관계를 추가할 때 어디에 무엇을 수정해야 하는지**를 계층별로 정리한 절차 문서입니다.

---

## 1. 시나리오 예시

`Memo`(메모) 하나에 여러 개의 `Comment`(댓글)가 달리는 **1:N 관계**를 추가한다고 가정합니다.

```text
Memo (1) ──────< Comment (N)
```

---

## 2. 계층별 수정 절차 (Top-down)

### Step 1: `models/` — ForeignKey와 relationship 정의

연관관계의 **핵심 수정 지점은 ORM 모델 계층**입니다.

**(1) 새 모델 파일 생성 — `models/comment.py`**

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # [핵심 1] ForeignKey: 자식(N) 테이블에 부모(1) 테이블의 PK를 참조하는 컬럼을 추가
    memo_id = Column(Integer, ForeignKey("memos.id", ondelete="CASCADE"), nullable=False)

    # [핵심 2] relationship: 객체 수준의 양방향 탐색 경로 정의 (comment.memo)
    memo = relationship("Memo", back_populates="comments")
```

**(2) 기존 모델 수정 — `models/memo.py`**

```python
from sqlalchemy.orm import relationship

class Memo(Base):
    __tablename__ = "memos"
    # ... 기존 컬럼 유지 ...

    # [핵심 3] 부모 쪽 relationship: memo.comments 로 자식 목록 접근
    # cascade 옵션으로 메모 삭제 시 댓글도 함께 삭제
    comments = relationship(
        "Comment",
        back_populates="memo",
        cascade="all, delete-orphan",
    )
```

**(3) 메타데이터 등록 — `main.py`**

```python
# Base.metadata.create_all(bind=engine) 이 새 테이블을 인식하도록 임포트 추가
import models.memo
import models.comment   # ← 추가
```

### Step 2: `schemas/` — 연관 데이터 DTO 정의

`schemas/comment.py`를 생성하고, 필요 시 부모 DTO에 자식 목록 필드를 추가합니다.

```python
# schemas/comment.py
class CommentResponse(BaseModel):
    id: int
    content: str
    memo_id: int
    model_config = ConfigDict(from_attributes=True)

# schemas/memo.py — 상세 응답에 댓글 목록 포함이 필요할 때
class MemoDetailResponse(MemoResponse):
    comments: List[CommentResponse] = []
```

### Step 3: `repositories/` — 연관 데이터 쿼리 추가

`repositories/comment_repository.py`를 생성합니다. 조인 조회가 필요하면 N+1 문제를 피하기 위해 `selectinload`/`joinedload`를 사용합니다.

```python
from sqlalchemy.orm import selectinload

def get_memo_with_comments(self, memo_id: int):
    return (
        self.db.query(Memo)
        .options(selectinload(Memo.comments))  # N+1 방지 즉시 로딩
        .filter(Memo.id == memo_id)
        .first()
    )
```

### Step 4: `services/` → `routers/` → `templates/`

| 계층 | 수정 내용 |
|---|---|
| `services/` | `CommentService` 추가 또는 `MemoService`에 댓글 유스케이스 추가 (검증 + DTO 변환) |
| `routers/` | `POST /memos/{id}/comments` 등 자식 리소스 엔드포인트 추가 (PRG 303 동일 적용) |
| `templates/` | `memo_detail.html`에 댓글 목록/작성 폼 렌더링 추가 |

---

## 3. 기존 DB에 반영하기 (마이그레이션 단계)

`Base.metadata.create_all()`은 **없는 테이블만 새로 만들 뿐, 기존 테이블 구조는 변경하지 못합니다.** 이미 데이터가 있는 `database.db`에 관계를 반영하는 방법은 두 가지입니다.

### 방법 A: 학습/개발 단계 — DB 재생성 (가장 간단)

```bash
# 1. 서버 중지 후 기존 DB 삭제 (데이터가 사라져도 되는 경우만!)
rm database.db
# 2. 서버 재기동 → create_all이 memos + comments 테이블을 새로 생성
uvicorn main:app --reload
```

### 방법 B: 데이터 보존 — 수동 마이그레이션 SQL

```bash
sqlite3 database.db <<'SQL'
-- 새 자식 테이블 생성 (models/comment.py 정의와 일치해야 함)
CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    content VARCHAR NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    memo_id INTEGER NOT NULL REFERENCES memos(id) ON DELETE CASCADE
);
CREATE INDEX ix_comments_id ON comments (id);
SQL
```

### 방법 C: 운영 확장 — Alembic 도입 (미션 이후)

```bash
pip install alembic            # ⚠️ 미션 제약(외부 라이브러리 금지) 해제 이후에만
alembic init migrations
# alembic/env.py에 target_metadata = Base.metadata 연결 후
alembic revision --autogenerate -m "add comments table"
alembic upgrade head
```

---

## 4. 주의 사항

- **삭제 정책 결정:** 부모 삭제 시 자식 처리(CASCADE / RESTRICT / SET NULL)를 반드시 먼저 결정합니다. SQLite에서는 `PRAGMA foreign_keys=ON` 활성화가 필요할 수 있습니다.
- **지연 로딩(Lazy Loading) 함정:** 세션이 닫힌 뒤 템플릿에서 `memo.comments`에 접근하면 `DetachedInstanceError`가 발생합니다. Repository에서 즉시 로딩하거나 DTO 변환을 세션 범위 내에서 완료해야 합니다.
- **마이그레이션:** `create_all`은 기존 테이블에 컬럼을 추가하지 못하므로, 실제 운영 확장 시 Alembic 같은 마이그레이션 도구 도입을 검토합니다. (본 미션에서는 외부 라이브러리 금지로 미사용)
