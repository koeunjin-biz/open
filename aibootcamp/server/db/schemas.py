from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# DTO 클래스 정의
class AdviceItemDto(BaseModel):
    topic: str
    messages: str  # JSON 문자열
    docs: Optional[str] = None  # JSON 문자열


class AdviceItemCreate(AdviceItemDto):
    pass


class AdviceItemSchema(AdviceItemDto):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
