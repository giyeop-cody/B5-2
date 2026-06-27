from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# [이유 및 목적] 메모 생성 및 수정을 위한 기본 데이터 교환 객체(DTO) 정의
# [이점] Pydantic을 활용하여 클라이언트 입력값의 타입 검증 및 유효성을 확보하고, 라우터나 서비스로 잘못된 데이터가 전달되는 것을 차단함.
class MemoBase(BaseModel):
    title: str = Field(..., title="메모 제목", min_length=1, description="메모의 제목은 비어 있을 수 없습니다.")
    content: str = Field(..., title="메모 내용", min_length=1, description="메모의 내용은 비어 있을 수 없습니다.")

# [이유 및 목적] 메모 생성을 위한 전용 스키마
# [이점] 생성 시 필요한 데이터 규격과 수정 시 필요한 데이터 규격을 분리하여 유연한 확장이 가능함.
class MemoCreate(MemoBase):
    pass

# [이유 및 목적] 메모 수정을 위한 전용 스키마
# [이점] 향후 수정 시 일부 필드만 선택적으로 변경(Optional)하도록 요구사항이 바뀌어도 손쉽게 수정 가능함.
class MemoUpdate(MemoBase):
    pass

# [이유 및 목적] 서버에서 클라이언트나 템플릿으로 데이터를 응답할 때 사용하는 DTO
# [이점] ORM 모델 객체를 안전하게 직렬화하며, 템플릿 렌더링 시 필요한 필수 정보(id, 생성/수정일시)만 명시적으로 노출함.
class MemoResponse(MemoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        # [이유 및 목적] SQLAlchemy ORM 모델 객체를 직접 읽어 Pydantic 스키마로 변환할 수 있도록 허용 (pydantic v2 기준)
        # [이점] DB 조회 결과를 손쉽게 DTO로 디커플링(Decoupling)하여 템플릿 및 라우터에 반환 가능
        from_attributes = True
