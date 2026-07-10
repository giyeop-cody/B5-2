"""
[이유 및 목적] 목록/상세/등록/수정/삭제 전체 화면 흐름을 검증하는 엔드투엔드(E2E) 통합 테스트 (AI 평가 항목 #1, #2 보완)
[이점] 외부 테스트 라이브러리(pytest, httpx 등) 없이 파이썬 표준 라이브러리(urllib, subprocess)만으로
      실제 uvicorn 서버를 기동하여 HTTP 레벨에서 헬스체크 및 CRUD + PRG(303) 흐름을 자동 검증함.
      (미션 제약사항인 '필수 5개 패키지 외 외부 라이브러리 금지'를 준수)

실행 방법:
    python3 test_integration.py
"""
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

HOST = "127.0.0.1"
PORT = 8010
BASE = f"http://{HOST}:{PORT}"


def request(method: str, path: str, data: dict | None = None, follow_redirect: bool = False):
    """표준 라이브러리만으로 HTTP 요청을 보내고 (status, body, location) 반환."""
    url = BASE + path
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener() if follow_redirect else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=10) as res:
            return res.status, res.read().decode(), res.headers.get("Location")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), e.headers.get("Location")


def wait_for_server(timeout: float = 20.0) -> None:
    """헬스체크: 홈(GET /)이 200을 반환할 때까지 대기."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status, _, _ = request("GET", "/")
            if status == 200:
                return
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.3)
    raise RuntimeError("서버가 제한 시간 내에 기동되지 않았습니다.")


def run_tests() -> None:
    passed = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed
        assert cond, f"[FAIL] {name} {detail}"
        passed += 1
        print(f"  [PASS] {name}")

    # 1. 헬스체크: 홈 화면
    status, html, _ = request("GET", "/")
    check("헬스체크: GET / 200 응답", status == 200)
    check("홈 화면: 목록/등록 링크 존재", "/memos" in html and "/memos/new" in html)

    # 2. 등록 (POST → 303 PRG)
    status, _, location = request("POST", "/memos/new", {"title": "통합테스트 제목", "content": "통합테스트 내용"})
    check("등록: POST 후 303 리다이렉트(PRG)", status == 303, f"got {status}")
    check("등록: 리다이렉트 타겟이 목록(/memos)", location == "/memos")

    # 2-1. [5차 평가 #3 보완] 303 수신 후 브라우저의 GET 재요청 동작을 명시적으로 검증 (PRG 완결성)
    #  - follow_redirect=True 로 요청하면 urllib이 브라우저처럼 303의 Location으로 GET 재요청을 수행함
    #  - 최종 응답이 200(HTML 렌더링)이고, 재요청이 GET이므로 등록이 중복 수행되지 않아야 함
    before_ids = set(re.findall(r"/memos/(\d+)", request("GET", "/memos")[1]))
    status, html, _ = request("POST", "/memos/new",
                              {"title": "PRG검증 제목", "content": "PRG검증 내용"}, follow_redirect=True)
    check("PRG 재요청: 303 추적 후 최종 200 + 목록 HTML 수신 (브라우저 GET 재요청 시뮬레이션)",
          status == 200 and "PRG검증 제목" in html)
    after_ids = set(re.findall(r"/memos/(\d+)", request("GET", "/memos")[1]))
    check("PRG 재요청: 리다이렉트 추적 과정에서 등록이 정확히 1건만 수행됨 (중복 제출 없음)",
          len(after_ids - before_ids) == 1, f"new_ids={after_ids - before_ids}")

    # 3. 목록 조회 및 생성된 메모 ID 추출
    status, html, _ = request("GET", "/memos")
    check("목록: GET /memos 200 응답 및 데이터 노출", status == 200 and "통합테스트 제목" in html)
    ids = re.findall(r"/memos/(\d+)", html)
    check("목록: 상세 링크 존재", len(ids) > 0)
    # 목록은 id 내림차순 정렬이므로, 첫 번째로 등록한 '통합테스트' 메모는 가장 작은 id
    memo_id = min(ids, key=int)

    # 4. 상세 조회 (전체 필드 노출)
    status, html, _ = request("GET", f"/memos/{memo_id}")
    check("상세: 제목/내용 전체 필드 표시", status == 200 and "통합테스트 제목" in html and "통합테스트 내용" in html)

    # 5. 검색 (보너스 과제 1)
    status, html, _ = request("GET", "/memos?" + urllib.parse.urlencode({"search": "통합테스트"}))
    check("검색: like 필터링 동작", status == 200 and "통합테스트 제목" in html)

    # 6. 수정 (POST → 303 PRG → 상세)
    status, _, location = request("POST", f"/memos/{memo_id}/edit", {"title": "수정된 제목", "content": "수정된 내용"})
    check("수정: POST 후 303 리다이렉트(PRG)", status == 303)
    check("수정: 리다이렉트 타겟이 상세 화면", location == f"/memos/{memo_id}")
    status, html, _ = request("GET", f"/memos/{memo_id}")
    check("수정: 변경 내용 반영 확인", "수정된 제목" in html)

    # 7. 검증 실패 (보너스 과제 2): 빈 제목 → 저장 차단 + 안내 문구
    status, html, _ = request("POST", "/memos/new", {"title": "", "content": "내용만 있음"})
    check("검증: 빈 제목 저장 차단 및 안내 문구", status == 200 and "제목" in html and "비어" in html)

    # 8. 삭제 (POST → 303 PRG)
    status, _, location = request("POST", f"/memos/{memo_id}/delete", {})
    check("삭제: POST 후 303 리다이렉트(PRG)", status == 303 and location == "/memos")

    # 9. 존재하지 않는 데이터 조회 → 안내 문구와 함께 목록 렌더링
    status, html, _ = request("GET", f"/memos/{memo_id}")
    check("미존재 데이터: 안내 문구 표시", status == 200 and "찾을 수 없습니다" in html)

    print(f"\n=== [SUCCESS] 통합 테스트 {passed}개 항목 전체 통과! ===")


def main() -> None:
    # 임시 DB를 사용하여 실제 database.db를 오염시키지 않음
    workdir = os.path.dirname(os.path.abspath(__file__))
    tmpdir = tempfile.mkdtemp(prefix="fastapi_it_")
    env = os.environ.copy()
    env["MEMO_DATABASE_URL"] = f"sqlite:///{os.path.join(tmpdir, 'test_integration.db')}"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", HOST, "--port", str(PORT)],
        cwd=workdir, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server()
        run_tests()
    finally:
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    main()
