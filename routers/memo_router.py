import os
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.memo_service import MemoService

# [이유 및 목적] 모듈화된 라우터 인스턴스 생성
# [이점] 애플리케이션의 엔드포인트를 깔끔하게 관리하고, 메인 파일(main.py)의 비대화를 방지함.
router = APIRouter()

# [이유 및 목적] Jinja2 템플릿 엔진 설정 (templates 디렉터리 지정)
# [이점] SSR(Server-Side Rendering) 구조를 활성화하여 동적 HTML 문서를 직접 생성 및 반환할 수 있음.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# [이유 및 목적] 홈 화면 엔드포인트 (GET /)
# [이점] 앱의 목적을 설명하는 문장과 주요 기능(목록, 등록)으로 이동할 수 있는 링크를 제공하여 웹 서비스의 진입점 역할을 함.
@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


# [이유 및 목적] 메모 목록 조회 및 검색 엔드포인트 (GET /memos)
# [이점] 선택적 쿼리 파라미터(search)를 지원하여 전체 목록 조회 및 키워드 검색을 한 번에 해결하며, 에러 메시지(error_msg)가 전달될 경우 화면에 표시할 수 있음.
@router.get("/memos", response_class=HTMLResponse)
async def read_memos(
    request: Request,
    search: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: Session = Depends(get_db)
):
    memos = MemoService.get_all_memos(db, search=search)
    return templates.TemplateResponse(
        "memo_list.html",
        {"request": request, "memos": memos, "search": search, "error_msg": error_msg}
    )


# [이유 및 목적] 새 메모 작성 폼 렌더링 엔드포인트 (GET /memos/new)
# [이점] 사용자에게 새로운 메모를 입력할 수 있는 HTML 폼 양식을 안전하게 제공함.
@router.get("/memos/new", response_class=HTMLResponse)
async def new_memo_form(request: Request):
    return templates.TemplateResponse("memo_form.html", {"request": request})


# [이유 및 목적] 폼 기반 새 메모 등록 처리 엔드포인트 (POST /memos/new)
# [이점] 반드시 POST 방식으로 Form 데이터를 수신하며, 성공 시 PRG 패턴(status_code=303)을 적용해 새로고침 중복 전송을 방지함. 실패 시 에러 메시지와 함께 폼 화면을 재렌더링함(보너스 과제 2).
@router.post("/memos/new", response_class=HTMLResponse)
async def create_memo(
    request: Request,
    title: str = Form(""),
    content: str = Form(""),
    db: Session = Depends(get_db)
):
    success, result = MemoService.create_memo(db, title=title, content=content)
    if not success:
        # result는 에러 메시지 문자열
        return templates.TemplateResponse(
            "memo_form.html",
            {"request": request, "error_msg": result, "title": title, "content": content}
        )
    # PRG 패턴 적용: 성공 시 목록 화면으로 303 Redirect
    return RedirectResponse(url="/memos", status_code=303)


# [이유 및 목적] 특정 메모 단건 상세 조회 엔드포인트 (GET /memos/{memo_id})
# [이점] 전체 필드와 수정/삭제/목록 이동 링크를 렌더링하며, 존재하지 않는 데이터 조회 시 오류 안내 메시지("해당 데이터를 찾을 수 없습니다")와 함께 목록 화면으로 처리함.
@router.get("/memos/{memo_id}", response_class=HTMLResponse)
async def read_memo_detail(request: Request, memo_id: int, db: Session = Depends(get_db)):
    memo = MemoService.get_memo_by_id(db, memo_id)
    if not memo:
        # 존재하지 않는 데이터 조회 시 적절한 안내 화면 표시 및 목록 이동 처리
        memos = MemoService.get_all_memos(db)
        return templates.TemplateResponse(
            "memo_list.html",
            {
                "request": request,
                "memos": memos,
                "error_msg": "해당 데이터를 찾을 수 없습니다."
            }
        )
    return templates.TemplateResponse("memo_detail.html", {"request": request, "memo": memo})


# [이유 및 목적] 기존 메모 수정 폼 렌더링 엔드포인트 (GET /memos/{memo_id}/edit)
# [이점] 기존 데이터를 폼에 채워 넣어(Pre-fill) 사용자 경험(UX)을 극대화함.
@router.get("/memos/{memo_id}/edit", response_class=HTMLResponse)
async def edit_memo_form(request: Request, memo_id: int, db: Session = Depends(get_db)):
    memo = MemoService.get_memo_by_id(db, memo_id)
    if not memo:
        memos = MemoService.get_all_memos(db)
        return templates.TemplateResponse(
            "memo_list.html",
            {"request": request, "memos": memos, "error_msg": "해당 데이터를 찾을 수 없습니다."}
        )
    return templates.TemplateResponse("memo_edit.html", {"request": request, "memo": memo})


# [이유 및 목적] 폼 기반 기존 메모 수정 처리 엔드포인트 (POST /memos/{memo_id}/edit)
# [이점] POST 방식으로 수신 및 성공 시 303 Redirect로 상세 화면 이동. 빈 값 등 검증 실패 시 에러 메시지 렌더링.
@router.post("/memos/{memo_id}/edit", response_class=HTMLResponse)
async def update_memo(
    request: Request,
    memo_id: int,
    title: str = Form(""),
    content: str = Form(""),
    db: Session = Depends(get_db)
):
    success, result = MemoService.update_memo(db, memo_id, title=title, content=content)
    if not success:
        # 에러 발생 시 기존 입력값과 에러 문구를 담아 수정 폼 재렌더링
        # 템플릿 호환을 위해 memo 객체 구조를 딕셔너리로 시뮬레이션
        temp_memo = {"id": memo_id, "title": title, "content": content}
        return templates.TemplateResponse(
            "memo_edit.html",
            {"request": request, "memo": temp_memo, "error_msg": result}
        )
    # PRG 패턴 적용: 성공 시 상세 화면으로 303 Redirect
    return RedirectResponse(url=f"/memos/{memo_id}", status_code=303)


# [이유 및 목적] 메모 삭제 처리 엔드포인트 (POST /memos/{memo_id}/delete)
# [이점] 삭제를 GET이 아닌 POST로 처리하여 안전성을 확보하고, 작업 완료 후 목록 화면으로 303 Redirect하여 PRG 패턴을 완벽히 구현함.
@router.post("/memos/{memo_id}/delete", response_class=HTMLResponse)
async def delete_memo(request: Request, memo_id: int, db: Session = Depends(get_db)):
    success = MemoService.delete_memo(db, memo_id)
    if not success:
        memos = MemoService.get_all_memos(db)
        return templates.TemplateResponse(
            "memo_list.html",
            {"request": request, "memos": memos, "error_msg": "해당 데이터를 찾을 수 없습니다."}
        )
    return RedirectResponse(url="/memos", status_code=303)
