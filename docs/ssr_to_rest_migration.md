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

---

## 6. 전환 체크리스트 (테스트·호환성)

### 6.1. 엔드포인트/계약(Contract)
- [ ] 모든 SSR 화면 흐름에 대응하는 REST 엔드포인트가 정의되었는가? (§3 매핑표 기준)
- [ ] `response_model`(Pydantic)로 응답 스키마가 명세되고 `/docs`(Swagger)에 노출되는가?
- [ ] 상태 코드 계약 준수: 등록 `201`, 삭제 `204`, 미존재 `404`, 검증 실패 `422`
- [ ] 페이지네이션/정렬 파라미터 정책이 정의되었는가? (SSR에는 없던 신규 관심사)

### 6.2. 보안
- [ ] **CORS:** 프론트 오리진(예: `http://localhost:3000`)을 `CORSMiddleware`의 `allow_origins`에 등록했는가? (와일드카드 `*`와 credentials 동시 사용 금지)
- [ ] **CSRF:** 쿠키 기반 인증을 유지한다면 CSRF 토큰 또는 `SameSite` 쿠키 정책이 필요. 토큰(JWT) 헤더 인증으로 가면 CSRF 부담이 줄어드는 대신 XSS 대비 토큰 저장 위치(메모리 권장) 검토
- [ ] 에러 응답에 내부 구현 정보(스택 트레이스, SQL)가 노출되지 않는가?

### 6.3. 테스트
- [ ] 기존 `test_mock_driver.py`(Service/Repository 단위)는 **수정 없이 그대로 통과**해야 함 — 레이어 분리 덕분에 전환의 회귀 기준선 역할
- [ ] `test_integration.py`를 REST 버전으로 복제: HTML 파싱 대신 JSON 응답·상태 코드(201/204/404/422) 검증으로 교체
- [ ] PRG 검증(303) 테스트는 REST에서는 제거하고, 프론트 라우팅 테스트로 대체
- [ ] SSR·REST 병행 기간에는 두 테스트를 모두 CI에서 실행

### 6.4. 정리 단계
- [ ] 프론트 전환 완료 후 SSR 라우터·`templates/` 제거
- [ ] `jinja2`, (파일 업로드 미사용 시) `python-multipart` 의존성 제거 및 `requirements.txt` 갱신
- [ ] README의 실행법·아키텍처 다이어그램을 REST 기준으로 갱신

---

## 7. 순서별 마이그레이션 체크리스트 (실행 순서 그대로)

§6이 관점별 점검표라면, 이 절은 **실제 작업 순서**대로 따라가는 단계별 체크리스트입니다.

### Phase 1 — API 병행 추가 (SSR 무중단)
- [ ] 1. `routers/api/memo_api_router.py` 생성 — `/api/memos` CRUD 엔드포인트 (Service/Repository 재사용)
- [ ] 2. 응답 계약 확정 — `response_model=MemoResponse`, 상태 코드 매핑: 등록 `201` / 수정 `200` / 삭제 `204` / 미존재 `404` / 검증 실패 `422`
- [ ] 3. 에러 응답 형식 통일 — `HTTPException(detail=...)` JSON 규격 (`{"detail": "..."}`), 내부 정보(SQL/스택) 미노출 확인
- [ ] 4. `main.py`에 API 라우터 등록 → `/docs`(Swagger)에서 계약 노출 확인

### Phase 2 — 프론트엔드 연동
- [ ] 5. CORS 설정 — `CORSMiddleware`에 프론트 오리진 등록 (와일드카드 `*` + credentials 동시 사용 금지)
- [ ] 6. 프론트 라우팅으로 화면 전환 대체 — PRG(303)는 API에서 제거, 성공 시 상태 코드만 반환
- [ ] 7. 폼 → JSON 전환 — `Form()` 파라미터 대신 Pydantic Body 수신, 프론트는 `fetch`/`axios`로 JSON 전송
- [ ] 8. 인증 필요 시 토큰 방식(JWT 등) 검토 — 쿠키 유지 시 CSRF(SameSite/토큰) 대비

### Phase 3 — 테스트 전환
- [ ] 9. `test_mock_driver.py`(Service/Repository 단위)는 **수정 없이 통과** 확인 → 회귀 기준선
- [ ] 10. `test_integration.py`를 REST 버전으로 복제 — HTML 파싱 대신 JSON·상태 코드(201/204/404/422) 검증
- [ ] 11. SSR·REST 병행 기간에는 두 테스트 모두 CI에서 실행

### Phase 4 — SSR 제거 및 정리
- [ ] 12. 프론트 전환 완료 후 SSR 라우터와 `templates/` 삭제
- [ ] 13. `jinja2`(및 파일 업로드 미사용 시 `python-multipart`) 의존성 제거, `requirements.txt` 갱신
- [ ] 14. README 실행법·아키텍처 다이어그램을 REST 기준으로 갱신
- [ ] 15. 최종 스모크 테스트 — `/docs` 정상 노출, 전체 CRUD JSON 흐름, CORS preflight(OPTIONS) 응답 확인
