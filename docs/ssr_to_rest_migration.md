# SSR → REST API 전환 가이드 (영향 분석)

> 본 문서는 AI 사전평가 보완 요구(평가 항목 #18)에 따라, 현재 **Jinja2 SSR 기반** 애플리케이션을 **REST API + 프론트엔드(SPA)** 구조로 전환할 때의 변경 지점과 영향 범위를 정리한 문서입니다.

---

## 1. 전환 전/후 아키텍처 비교

```text
[현재: SSR]                              [전환 후: REST + SPA]
브라우저                                  브라우저 (React/Vue 등 JS 앱)
   │  GET/POST (HTML Form)                  │  fetch/axios (JSON)
   ▼                                        ▼
Router ── TemplateResponse(HTML)         Router ── JSONResponse (Pydantic 직렬화)
   │                                        │
Service / Repository (변경 없음) ◄──────── Service / Repository (변경 없음)
```

**핵심 결론: 계층 분리 덕분에 Service / Repository / Model 계층은 코드 수정이 거의 없고, 변경은 Router와 Templates에 집중됩니다.** 이것이 본 프로젝트가 레이어 분리를 채택한 실질적 이점입니다.

---

## 2. 계층별 변경 영향

| 계층 | 영향도 | 변경 내용 |
|---|---|---|
| `templates/` | 🔴 제거 | Jinja2 템플릿 전체 삭제. 화면은 별도 프론트엔드 프로젝트(React/Vue 등)가 담당 |
| `routers/` | 🔴 대폭 수정 | `TemplateResponse` → JSON 응답, `Form()` → Pydantic Body, PRG 리다이렉트 → HTTP 상태 코드 |
| `schemas/` | 🟡 소폭 수정 | 이미 Pydantic DTO 구조이므로 `response_model`로 그대로 재사용 |
| `services/` | 🟢 변경 없음 | 비즈니스 로직은 HTTP 표현 방식과 무관 |
| `repositories/` | 🟢 변경 없음 | DB 접근 로직은 그대로 유지 |
| `models/` | 🟢 변경 없음 | ORM 모델 그대로 유지 |
| 의존성 | 🟡 정리 | `jinja2`, `python-multipart`(Form 파싱용) 제거 가능 |

---

## 3. 엔드포인트 매핑 변경표

SSR에서는 HTML Form이 GET/POST만 지원하므로 POST로 통일했지만, REST에서는 HTTP 메서드 시맨틱을 온전히 사용합니다.

| 기능 | 현재 (SSR) | 전환 후 (REST) |
|---|---|---|
| 목록 조회 | `GET /memos` → HTML | `GET /api/memos` → `200` + JSON 배열 |
| 상세 조회 | `GET /memos/{id}` → HTML | `GET /api/memos/{id}` → `200` / **`404`** |
| 등록 폼 | `GET /memos/new` → HTML | ❌ 불필요 (프론트가 화면 담당) |
| 등록 | `POST /memos/new` (Form) → `303` | `POST /api/memos` (JSON Body) → **`201 Created`** |
| 수정 폼 | `GET /memos/{id}/edit` → HTML | ❌ 불필요 |
| 수정 | `POST /memos/{id}/edit` (Form) → `303` | **`PUT/PATCH`** `/api/memos/{id}` → `200` |
| 삭제 | `POST /memos/{id}/delete` (Form) → `303` | **`DELETE`** `/api/memos/{id}` → **`204 No Content`** |

---

## 4. 주요 패턴 전환 포인트

### 4.1. PRG 패턴 → 상태 코드 기반 응답

- SSR의 PRG(303 리다이렉트)는 **브라우저 새로고침 중복 제출**을 막기 위한 것입니다.
- REST에서는 서버가 화면을 이동시키지 않으므로 PRG가 필요 없습니다. 대신 `201`/`204` 등 정확한 상태 코드를 반환하고, **화면 전환은 프론트엔드 라우터**(React Router 등)가 담당합니다.

### 4.2. Form() → Pydantic Body

```python
# 현재 (SSR): Form 파라미터 수신
async def create_memo(title: str = Form(""), content: str = Form("")): ...

# 전환 후 (REST): Pydantic 모델을 Body로 수신 — 자동 검증 + 422 응답
@router.post("/api/memos", response_model=MemoResponse, status_code=201)
async def create_memo(payload: MemoCreate, service: MemoService = Depends(get_memo_service)): ...
```

### 4.3. 에러 표시 → HTTPException

- 현재: 오류 시 `error_msg`를 템플릿에 담아 재렌더링
- 전환 후: `raise HTTPException(status_code=404, detail="해당 데이터를 찾을 수 없습니다.")` → 프론트가 JSON 에러를 받아 UI에 표시. 검증 실패는 Pydantic이 자동으로 `422`를 반환

### 4.4. 프론트엔드 측 신규 고려사항

- **CORS 설정:** 프론트가 다른 오리진에서 서빙되면 `CORSMiddleware` 추가 필요
- **API 문서:** FastAPI 자동 문서(`/docs`, Swagger UI)가 프론트 개발자와의 계약(Contract) 역할 수행
- **인증:** SSR 세션/쿠키 대신 토큰 기반(JWT 등) 인증 검토 (다음 미션 범위)

---

## 5. 점진적 전환 전략 (권장)

1. 기존 SSR 라우터를 유지한 채 `routers/api/` 아래에 `/api/memos` REST 라우터를 **병행 추가**
2. Service/Repository를 공유하므로 로직 중복 없음
3. 프론트엔드 개발 완료 후 SSR 라우터와 `templates/` 제거, `jinja2` 의존성 정리
