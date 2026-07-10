import os
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from repositories.memo_repository import MemoRepository
from services.memo_service import MemoService
from services.result import ServiceResult

# [이유 및 목적] 모듈화된 라우터 인스턴스 생성
# [이점] 엔드포인트를 모듈화하여 메인 파일(main.py)의 책임을 최소화하고 유지보수성을 극대화함.
router = APIRouter()

# [이유 및 목적] Jinja2 템플릿 엔진 설정 (templates 디렉터리 지정)
# [이점] SSR(Server-Side Rendering) 구조를 활성화하여 동적 HTML 문서를 직접 생성 및 반환할 수 있음.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# [이유 및 목적] MemoService 의존성 주입 팩토리 함수 정의 (Clean Architecture 및 Affinity 관리)
# [이점] FastAPI의 Depends를 활용하여 DB 세션을 MemoRepository에 주입하고, 이를 다시 MemoService에 주입하는 조립(Wiring) 과정을 팩토리 함수 한 곳에 응집(Affinity)시킴. 라우터 함수들은 생성된 MemoService 인스턴스만 주입받으면 되므로 코드가 극도로 깔끔해짐.
def get_memo_service(db: Session = Depends(get_db)) -> MemoService:
    repository = MemoRepository(db)
    return MemoService(repository)


# [이유 및 목적] 홈 화면 엔드포인트 (GET /)
# [이점] 앱의 목적을 설명하는 문장과 주요 기능(목록, 등록)으로 이동할 수 있는 링크를 제공하여 웹 서비스의 진입점 역할을 함.
@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse(request, "home.html")


# [이유 및 목적] 메모 목록 조회 및 검색 엔드포인트 (GET /memos)
# [이점] 선택적 쿼리 파라미터(search)를 지원하여 전체 목록 조회 및 키워드 검색을 한 번에 해결하며, 주입받은 service 인스턴스를 통해 DB 세션 노출 없이 데이터를 조회함.
@router.get("/memos", response_class=HTMLResponse)
async def read_memos(
    request: Request,
    search: Optional[str] = None,
    error_msg: Optional[str] = None,
    service: MemoService = Depends(get_memo_service)
):
    memos = service.get_all_memos(search=search)
    return templates.TemplateResponse(
        request,
        "memo_list.html",
        {"memos": memos, "search": search, "error_msg": error_msg}
    )


# [이유 및 목적] 새 메모 작성 폼 렌더링 엔드포인트 (GET /memos/new)
# [이점] 사용자에게 새로운 메모를 입력할 수 있는 HTML 폼 양식을 안전하게 제공함.
@router.get("/memos/new", response_class=HTMLResponse)
async def new_memo_form(request: Request):
    return templates.TemplateResponse(request, "memo_form.html")


# [이유 및 목적] 폼 기반 새 메모 등록 처리 엔드포인트 (POST /memos/new)
# [이점] ServiceResult 패턴을 활용하여 성공 시 303 PRG 리다이렉트, 실패 시 result.error 메시지와 함께 폼 화면을 재렌더링함(보너스 과제 2).
@router.post("/memos/new", response_class=HTMLResponse)
async def create_memo(
    request: Request,
    title: str = Form(""),
    content: str = Form(""),
    service: MemoService = Depends(get_memo_service)
):
    result = service.create_memo(title=title, content=content)
    if not result.success:
        return templates.TemplateResponse(
            request,
            "memo_form.html",
            {"error_msg": result.error, "title": title, "content": content}
        )
    # PRG 패턴 적용: 성공 시 목록 화면으로 303 Redirect
    return RedirectResponse(url="/memos", status_code=303)


# [이유 및 목적] 특정 메모 단건 상세 조회 엔드포인트 (GET /memos/{memo_id})
# [이점] 전체 필드와 수정/삭제/목록 이동 링크를 렌더링하며, 존재하지 않는 데이터 조회 시 오류 안내 메시지("해당 데이터를 찾을 수 없습니다")와 함께 목록 화면으로 처리함.
@router.get("/memos/{memo_id}", response_class=HTMLResponse)
async def read_memo_detail(request: Request, memo_id: int, service: MemoService = Depends(get_memo_service)):
    memo = service.get_memo_by_id(memo_id)
    if not memo:
        memos = service.get_all_memos()
        return templates.TemplateResponse(
            request,
            "memo_list.html",
            {"memos": memos, "error_msg": "해당 데이터를 찾을 수 없습니다."}
        )
    return templates.TemplateResponse(request, "memo_detail.html", {"memo": memo})


# [이유 및 목적] 기존 메모 수정 폼 렌더링 엔드포인트 (GET /memos/{memo_id}/edit)
# [이점] 기존 데이터를 폼에 채워 넣어(Pre-fill) 사용자 경험(UX)을 극대화함.
@router.get("/memos/{memo_id}/edit", response_class=HTMLResponse)
async def edit_memo_form(request: Request, memo_id: int, service: MemoService = Depends(get_memo_service)):
    memo = service.get_memo_by_id(memo_id)
    if not memo:
        memos = service.get_all_memos()
        return templates.TemplateResponse(
            request,
            "memo_list.html",
            {"memos": memos, "error_msg": "해당 데이터를 찾을 수 없습니다."}
        )
    return templates.TemplateResponse(request, "memo_edit.html", {"memo": memo})


# [이유 및 목적] 폼 기반 기존 메모 수정 처리 엔드포인트 (POST /memos/{memo_id}/edit)
# [이점] POST 방식으로 수신 및 성공 시 303 Redirect로 상세 화면 이동. ServiceResult 기반 에러 처리.
@router.post("/memos/{memo_id}/edit", response_class=HTMLResponse)
async def update_memo(
    request: Request,
    memo_id: int,
    title: str = Form(""),
    content: str = Form(""),
    service: MemoService = Depends(get_memo_service)
):
    result = service.update_memo(memo_id, title=title, content=content)
    if not result.success:
        temp_memo = {"id": memo_id, "title": title, "content": content}
        return templates.TemplateResponse(
            request,
            "memo_edit.html",
            {"memo": temp_memo, "error_msg": result.error}
        )
    # PRG 패턴 적용: 성공 시 상세 화면으로 303 Redirect
    return RedirectResponse(url=f"/memos/{memo_id}", status_code=303)


# [이유 및 목적] 메모 삭제 처리 엔드포인트 (POST /memos/{memo_id}/delete)
# [이점] 삭제를 POST로 처리하여 안전성을 확보하고, 작업 완료 후 목록 화면으로 303 Redirect하여 PRG 패턴을 완벽히 구현함.
@router.post("/memos/{memo_id}/delete", response_class=HTMLResponse)
async def delete_memo(request: Request, memo_id: int, service: MemoService = Depends(get_memo_service)):
    success = service.delete_memo(memo_id)
    if not success:
        memos = service.get_all_memos()
        return templates.TemplateResponse(
            request,
            "memo_list.html",
            {"memos": memos, "error_msg": "해당 데이터를 찾을 수 없습니다."}
        )
    return RedirectResponse(url="/memos", status_code=303)
