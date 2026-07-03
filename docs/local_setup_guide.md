# 🏠 FastAPI CRUD 프로젝트: 로컬(샌드박스 외부) 실행 가이드

> **목적**: 본 문서는 Arena.ai 샌드박스 낶부에서 개발·검증이 완료된 `fastapi_crud_project`를, 사용자의 로컬 PC(Windows·macOS·Linux)로 가져가 최종 실행·제출 준비를 할 때 필요한 절차를 상세히 기술합니다.
> **왜 필요한가**: 샌드박스는 외부 네트워크·브라우저·GUI 도구 사용에 제약이 있으므로, 가상환경 생성, 브라우저 접속, 스크린샷 촬영, GitHub 원격 푸시, SQLite 뷰어 사용 등은 반드시 사용자의 로컬 환경에서 수행해야 합니다.

---

## 1️⃣ 프로젝트 압축 해제

제공받은 `fastapi_crud_project.zip`을 로컬 원하는 위치(예: `C:\Users\사용자\Projects` 또는 `~/Projects`)에 해제합니다.

```text
fastapi_crud_project/
├── .git/                 ← git 커밋 히스토리 포함됨
├── docs/
├── models/
├── repositories/
├── routers/
├── schemas/
├── services/
├── templates/
├── .gitignore
├── database.db
├── database.py
├── main.py
├── README.md
├── requirements.txt
└── test_mock_driver.py
```

- `venv/` 폴터는 용량 문제로 압축에서 제외되었습니다. **로컬에서 직접 다시 생성**해야 합니다.
- `.git/` 폴터는 포함되어 있으므로, 해제 후 `git log --oneline` 등으로 전체 개발 이력을 확인할 수 있습니다.

---

## 2️⃣ Python 가상환경 생성 및 활성화

> **왜 가상환경인가**: 프로젝트별 의존성을 시스템 Python과 분리하여, 버전 충돌을 방지하고 과제 제약(`fastapi`, `uvicorn`, `sqlalchemy`, `jinja2`, `python-multipart` 5개만 사용)을 명확히 준수하기 위함입니다.

프로젝트 루트로 이동한 뒤 아래 명령 중 운영체제에 맞는 것을 실행합니다.

### Windows (PowerShell)

```powershell
cd fastapi_crud_project
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> PowerShell 실행 정책 오류 발생 시 관리자 권한 PowerShell에서 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` 실행 후 재시도하세요.

### Windows (CMD)

```cmd
cd fastapi_crud_project
python -m venv venv
venv\Scripts\activate.bat
```

### macOS / Linux

```bash
cd fastapi_crud_project
python3 -m venv venv
source venv/bin/activate
```

활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다.

---

## 3️⃣ 의존성 패키지 설치

> **왜 requirements.txt인가**: 미션에서 허용한 5개 패키지만 명시하여, 외부 라이브러리 추가 없이 동일한 실행 환경을 재현할 수 있게 합니다.

가상환경이 활성화된 상태에서 실행합니다.

```bash
pip install -r requirements.txt
```

`requirements.txt` 내용:

```text
fastapi
uvicorn
sqlalchemy
jinja2
python-multipart
```

설치 후 버전 확인 예시:

```bash
pip list
```

---

## 4️⃣ 서버 실행

> **왜 `main:app --reload`인가**: `main.py`의 FastAPI 인스턴스(`app`)를 Uvicorn ASGI 서버로 실행하며, 코드 변경 시 자동 재시작하는 개발 모드입니다.

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

정상 실행 시 터미널에 다음과 유사한 메시지가 출력됩니다.

```text
INFO:     Will watch for changes in '/.../fastapi_crud_project'
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 5️⃣ 브라우저에서 동작 확인

> **왜 로컬 브라우저인가**: 샌드박스 프리뷰는 외부 스타일시트·폰트 등이 차단되는 iframe 환경이므로, 실제 HTML 폼 전송·리다이렉트·CSS 레이아웃을 온전히 확인하려면 로컬 브라우저가 필요합니다.

웹 브라우저를 열고 아래 주소로 접속합니다.

```text
http://localhost:8000
```

확인할 화면:

| 순서 | 경로 | 설명 |
|------|------|------|
| 1 | `GET /` | 홈 화면 |
| 2 | `GET /memos/new` | 메모 등록 폼 |
| 3 | `POST /memos/new` | 등록 후 303 Redirect → 목록 |
| 4 | `GET /memos` | 메모 목록 + 검색 |
| 5 | `GET /memos/{id}` | 메모 상세 조회 |
| 6 | `GET /memos/{id}/edit` | 수정 폼 |
| 7 | `POST /memos/{id}/edit` | 수정 후 303 Redirect → 상세 |
| 8 | `POST /memos/{id}/delete` | 삭제 후 303 Redirect → 목록 |

---

## 6️⃣ Mock 드라이버 검증 (선택 권장)

> **왜 Mock 검증인가**: 실제 DB(`database.db`)에 영향을 주지 않고, 인메모리 SQLite에서 Repository·Service·ServiceResult 계층의 정합성을 빠르게 확인할 수 있습니다.

가상환경 활성화 상태에서:

```bash
python test_mock_driver.py
```

최종에 다음 메시지가 출력되면 성공입니다.

```text
=== [SUCCESS] 모든 리팩토링 및 Mock 드라이버 검증 테스트를 성공적으로 통과했습니다! ===
```

---

## 7️⃣ git 히스토리 및 브랜치 확인

> **왜 브랜치 전략을 확인하는가**: `master`는 제출용 최종본, `test`는 구현·Mock 검증용, `evel`은 중간 산출물·문서·평가용 브랜치입니다. 제출 전 반드시 현재 브랜치와 커밋 이력을 확인해야 합니다.

```bash
git log --oneline --all --graph
```

예상 출력:

```text
* a2aed62 (HEAD -> master, test, evel) refactor: apply Clean Architecture, Dependency Injection, SRP, and ServiceResult monad pattern
* a63cf19 docs: re-verification report of master branch and clean architecture refactoring design
* b56f83f feat: complete end-to-end FastAPI CRUD web service implementation with PRG pattern, ADR docs, and mock driver verification
* 664be46 docs: comprehensive task analysis, verification, project plan, and ADRs
* 132d76c chore: initial commit with baseline mission requirement documents
```

제출 시에는 `master` 브랜치를 기준으로 제출합니다.

---

## 8️⃣ GitHub 원격 저장소 연결 및 푸시 (제출 방식이 GitHub 링크일 경우)

> **왜 로컬에서 해야 하는가**: 샌드박스는 외부 GitHub 인증·SSH·개인 액세스 토큰 사용이 제한되므로, 원격 저장소 생성과 `push`는 로컬에서 수행해야 합니다.

1. GitHub 웹사이트에서 새 저장소를 생성합니다(예: `fastapi_crud_project`).
2. 로컬 프로젝트 루트에서 원격 저장소를 추가합니다.

```bash
git remote add origin https://github.com/<사용자명>/fastapi_crud_project.git
```

3. 모든 브랜치를 푸시합니다.

```bash
git push -u origin master
git push -u origin test
git push -u origin evel
```

> HTTPS 인증 시 GitHub 개인 액세스 토큰(PAT) 또는 GitHub CLI 로그인이 필요할 수 있습니다.

---

## 9️⃣ 스크린샷 촬영 (보너스·선택)

> **왜 로컬에서 촬영하는가**: 실제 브라우저에서 CSS가 적용된 상태의 화면을 캡처해야 하며, 샌드박스 프리뷰에서는 외부 리소스가 차단되어 실제 UI가 다르게 보일 수 있습니다.

촬영 권장 화면:

1. 홈 화면 (`/`)
2. 메모 등록 폼 (`/memos/new`)
3. 메모 목록 (`/memos`)
4. 메모 상세 (`/memos/{id}`)
5. 메모 수정 (`/memos/{id}/edit`)
6. 검색 결과 (`/memos?search=키워드`)
7. 빈값 검증 오류 메시지

캡처한 이미지는 프로젝트 루트의 `screenshots/` 폴더 등에 정리한 뒤, 필요하면 별도로 제출합니다.

---

## 🔟 SQLite 데이터베이스 확인 (선택)

> **왜 DB Browser인가**: 미션에서 언급된 바와 같이, `database.db` 파일을 직접 열어 테이블·데이터를 확인하는 것은 CRUD 동작의 정합성을 객관적으로 검증하는 좋은 방법입니다.

로컬에 [DB Browser for SQLite](https://sqlitebrowser.org/)를 설치한 뒤, 프로젝트 루트의 `database.db` 파일을 엽니다.

확인 항목:

- `memos` 테이블 존재 여부
- `id`, `title`, `content`, `created_at`, `updated_at` 컬럼
- 등록·수정·삭제 후 데이터 변화

---

## 📋 샌드박스 외부에서 반드시 수행해야 할 항목 요약

| 번호 | 항목 | 이유 |
|------|------|------|
| 1 | `fastapi_crud_project.zip` 해제 | 로컬에서 프로젝트를 열기 위함 |
| 2 | Python 가상환경 생성 및 활성화 | 의존성 격리 및 재현성 확보 |
| 3 | `pip install -r requirements.txt` | 5개 허용 패키지만 설치 |
| 4 | `uvicorn main:app --reload` 실행 | 실제 웹 서버 기동 |
| 5 | 브라우저에서 `http://localhost:8000` 접속 | 실제 UI·폼·리다이렉트 확인 |
| 6 | `python test_mock_driver.py` 실행 | 인메모리 Mock 기반 검증 |
| 7 | `git log --oneline` 확인 | 커밋 히스토리·브랜치 상태 확인 |
| 8 | GitHub 원격 저장소 생성 및 `git push` | GitHub 링크 제출 시 필요 |
| 9 | 주요 화면 스크린샷 촬영 | 제출 보조자료 및 보너스 평가 |
| 10 | DB Browser for SQLite로 `database.db` 확인 | 데이터 영속성 객관적 검증 |

---

## ⚠️ 주의사항

- **venv 폴더는 업로드/제출하지 마세요.** `.gitignore`에 이미 등록되어 있으며, 압축 파일에도 포함되지 않았습니다.
- **`.git/` 폴더를 삭제하지 마세요.** git 커밋 이력이 포함되어 있어야 과제 평가 시 개발 과정을 확인할 수 있습니다.
- **`database.db`는 샌드박스에서 생성된 샘플 DB입니다.** 로컬에서 새로 생성되어도 무방하며, `.gitignore`에 등록되어 있어 git에는 포함되지 않습니다.
- **Python 버전은 3.10 이상을 권장합니다.** 본 프로젝트는 Python 3.13 환경에서 개발되었습니다.

---

*문서 작성일: 2026-07-04*  
*작성자: Arena Agent*  
*연관 문서: `README.md`, `docs/re_verification_report.md`, `docs/clean_architecture_design.md`*
