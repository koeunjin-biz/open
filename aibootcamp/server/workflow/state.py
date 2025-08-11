"""
LangGraph 워크플로우 상태 정의

이 모듈은 LangGraph 워크플로우에서 사용하는 상태 타입들을 정의합니다.
AI 에이전트 간의 상담 상태와 RAG 검색 결과를 관리합니다.
"""

from typing import Dict, List, TypedDict


class AgentType:
    """에이전트 타입 정의"""
    IPO = "IPO_AGENT"  # KRX 상장심사 담당자 에이전트

#    @classmethod
#    def to_korean(cls, role: str) -> str:
#        """에이전트 역할을 한국어로 변환"""
#        return role


class AdviceState(TypedDict):
    """
    상담 상태 타입 정의
    
    LangGraph 워크플로우에서 사용하는 상태 구조를 정의합니다.
    """
    topic: str  # 상담 주제
    messages: List[Dict]  # 대화 내역 (역할, 내용 포함)
    prev_node: str  # 이전 실행된 노드
    docs: Dict[str, List]  # RAG 검색 결과 (에이전트별로 구분)
    contexts: Dict[str, str]  # RAG 검색 컨텍스트 (에이전트별로 구분)
