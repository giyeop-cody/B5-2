# [AI 사전평가] FAIL 2건 및 개선 권고 16건 보완 (89% → 100% 목표)

**평가 시각:** 2026-07-11 01:14:33 · **결과:** 16 / 18 통과 (89%)

AI 사전평가에서 지적된 FAIL 항목과 PASS 항목의 "부족한 점/보완" 권고를 전수 정리하고 수정한다.

## 🔴 FAIL 항목 (필수 수정)

### 항목 #17 — 모델 연관관계 문서 부재
- **부족한 점:** 모델 연관관계(relationship/ForeignKey) 추가 방법 및 예시가 제출물에 없음
- **조치:** `docs/model_relationships_guide.md` 신규 작성 — Memo:Comment 1:N 예시로 models → schemas → repositories → services/routers/templates 계층별 수정 지점, cascade/지연 로딩/마이그레이션 주의사항 정리

### 항목 #18 — SSR→REST 전환 영향 문서 부재
- **부족한 점:** SSR에서 REST로 전환할 때 템플릿→프론트 변경 영향 설명이 없음
- **조치:** `docs/ssr_to_rest_migration.md` 신규 작성 — 계층별 영향도표, 엔드포인트/HTTP 메서드 매핑 변경표, PRG→상태코드 전환, Form()→Body 전환, CORS 등 프론트 고려사항, 점진적 전환 전략 정리

## 🟡 PASS 항목의 개선 권고 (16건)

| # | 부족한 점 | 조치 |
|---|---|---|
| 1 | 자동화된 헬스체크/테스트 미포함 | `test_integration.py` E2E 테스트 + README curl 헬스체크 추가 |
| 2 | 통합(E2E) 테스트 미포함 | `test_integration.py` — 목록/상세/등록/수정/삭제/검색/검증 14개 항목 검증 (표준 라이브러리만 사용) |
| 3 | 리다이렉트 타겟/상태 일관성 문서 없음 | README에 POST별 303 타겟 정책(등록→목록, 수정→상세, 삭제→목록) 명시 |
| 4 | DB 파일 위치 변경 방법 없음 | `MEMO_DATABASE_URL` 환경변수 지원 + README 예시 |
| 5 | 404 응답 정책 미기재 | README에 안내 방식(목록 렌더링 채택 이유 vs REST 시 404) 명시 |
| 6 | 설치·실행 요약 부족 | README에 venv→설치→실행 한 블록 요약 + pip 오류 대처 추가 |
| 7 | 디렉터리별 대표 파일 설명 부족 | 구조도에 각 파일의 핵심 함수/책임 한 줄 설명 보강 |
| 8 | 서비스/저장소 경계 사례 미기재 | README에 트랜잭션 경계(커밋은 Repository) 책임 예시 추가 |
| 9 | 세션 rollback 예시 없음 | Repository `_commit()` 헬퍼(실패 시 rollback) + `get_db` 예외 시 rollback 추가 |
| 10 | 요청 흐름 다이어그램 없음 | README에 Router→Service→Repository→Template ASCII 다이어그램 추가 |
| 11 | REST 메서드 매핑 정책 없음 | README GET/POST 규칙 + `docs/ssr_to_rest_migration.md` 매핑표 |
| 12 | PRG 브라우저 동작 미기재 | README에 303 수신 시 브라우저 동작(GET 강제, 302 대비 이점) 요약 |
| 13 | 세션 라이프사이클 상세 부족 | README에 'HTTP 요청 1건 = 세션 1개' 및 트랜잭션 경계 설명 추가 |
| 14 | Form→Pydantic 변환 흐름 설명 부족 | README에 Form() → 검증 → MemoCreate/Update → MemoResponse 흐름 추가 |
| 15 | 레이어 미분리 문제 사례 없음 | README에 미분리 시 유지보수/테스트 문제 코드 레벨 예시 추가 |
| 16 | DB URL 환경변수화 없음 | #4와 동일 — `database.py` 환경변수 외부화 (SQLite 외 DB 대비 connect_args 조건부 처리) |

## ✅ 검증 결과
- `python3 test_mock_driver.py` → 전체 통과
- `python3 test_integration.py` → 14개 항목 전체 통과 (실제 uvicorn 기동, 임시 DB 사용)
- 호환성: 최신 Starlette의 `TemplateResponse(request, name, context)` 신규 시그니처로 이관 완료
