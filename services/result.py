from typing import Generic, TypeVar, Optional, Any

T = TypeVar("T")

# [이유 및 목적] 비즈니스 서비스 계층의 실행 결과를 표준화된 도메인 객체로 캡슐화하는 Result 패턴 정의
# [이점] Tuple[bool, Any] 방식의 모호함을 극복하고, 라우터 계층에서 성공/실패 여부와 데이터를 명확하고 가독성 높게 처리할 수 있음.
class ServiceResult(Generic[T]):
    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    # [이유 및 목적] 성공 시 결과 데이터를 담은 객체를 생성하는 팩토리 메소드
    # [이점] 인스턴스 생성을 직관적으로 만들어 코드 가독성을 대폭 향상함
    @classmethod
    def success(cls, data: T) -> "ServiceResult[T]":
        return cls(success=True, data=data)

    # [이유 및 목적] 실패 시 에러 메시지를 담은 객체를 생성하는 팩토리 메소드
    # [이점] 예외 처리를 디커플링하여 서버 에러 대신 템플릿에 출력할 사용자 친화적인 에러 메시지 반환 가능
    @classmethod
    def fail(cls, error: str) -> "ServiceResult[T]":
        return cls(success=False, error=error)
