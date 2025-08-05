# LangGraph 상태 정의 - RAG 관련 필드 추가
from typing import Dict, List, TypedDict


class AgentType:
    IPO = "IPO_AGENT"

    @classmethod
    def to_korean(cls, role: str) -> str:
            return role


class AdviceState(TypedDict):
    topic: str
    messages: List[Dict]
    prev_node: str
    docs: Dict[str, List]  # RAG 검색 결과
    contexts: Dict[str, str]  # RAG 검색 컨텍스트
