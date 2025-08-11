"""
워크플로우 API 라우터

이 모듈은 LangGraph 기반의 AI 워크플로우를 처리하는 API 엔드포인트를 제공합니다.
실시간 스트리밍 응답을 통해 사용자와 AI 에이전트 간의 상담을 지원합니다.

주요 기능:
- 스트리밍 상담 API
- LangGraph 워크플로우 실행
- Langfuse 모니터링 연동
"""

from typing import Any
import uuid
import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langfuse.callback import CallbackHandler


from workflow.state import AgentType, AdviceState
from workflow.graph import create_advice_graph


# API 경로를 /api/v1로 변경
router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["workflow"],
    responses={404: {"description": "Not found"}},
)


class WorkflowRequest(BaseModel):
    """워크플로우 요청 데이터 모델"""
    topic: str  # 상담 주제
    enable_rag: bool = True  # RAG(Retrieval-Augmented Generation) 활성화 여부


class WorkflowResponse(BaseModel):
    """워크플로우 응답 데이터 모델"""
    status: str = "success"  # 처리 상태
    result: Any = None  # 처리 결과


async def advice_generator(advice_graph, initial_state, langfuse_handler):
    """
    LangGraph 워크플로우에서 스트리밍 응답을 생성하는 제너레이터
    
    Args:
        advice_graph: LangGraph 컴파일된 워크플로우
        initial_state: 초기 상태
        langfuse_handler: Langfuse 콜백 핸들러
        
    Yields:
        str: Server-Sent Events 형식의 JSON 데이터
    """
    print(f"[START]workflow.advice_generator({advice_graph},{initial_state},{langfuse_handler})")
    
    # LangGraph 워크플로우에서 스트리밍 청크 처리
    for chunk in advice_graph.stream(
        initial_state,
        config={"callbacks": [langfuse_handler]},
        subgraphs=True,  # 서브그래프 정보 포함
        stream_mode="updates",  # 업데이트 모드로 스트리밍
    ):
        # 빈 청크 무시
        if not chunk:
            continue

        # 노드 정보 추출
        node = chunk[0] if len(chunk) > 0 else None
        if not node or node == ():
            continue

        # 노드 이름에서 역할 추출 (예: "IPO_AGENT:retrieve_context" -> "IPO_AGENT")
        node_name = node[0]
        role = node_name.split(":")[0]
        
        # 서브그래프에서 상태 정보 추출
        subgraph = chunk[1]
        subgraph_node = subgraph.get("update_state", None)

        if subgraph_node:
            # 응답 및 상태 정보 추출
            response = subgraph_node.get("response", None)  # AI 에이전트 응답
            advice_state = subgraph_node.get("advice_state", None)  # 전체 상담 상태
            messages = advice_state.get("messages", [])  # 대화 내역
            docs = advice_state.get("docs", {})  # 참고 자료
            topic = advice_state.get("topic")  # 상담 주제

            # 클라이언트로 전송할 상태 데이터 구성
            state = {
                "role": role,
                "response": response,
                "topic": topic,
                "messages": messages,
                "docs": docs,
            }

            # Server-Sent Events 형식으로 데이터 전송
            event_data = {"type": "update", "data": state}
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            print(event_data)

            # 스트리밍 간격 조절 (10ms)
            await asyncio.sleep(0.01)

    # 상담 종료 메시지 전송
    yield f"data: {json.dumps({'type': 'end', 'data': {}}, ensure_ascii=False)}\n\n"


# 엔드포인트 경로 수정 (/advice/stream -> 유지)
@router.post("/advice/stream")
async def stream_advice_workflow(request: WorkflowRequest):
    print(f"[START]workflow.stream_advice_workflow({request})")

    topic = request.topic
    enable_rag = request.enable_rag

    session_id = str(uuid.uuid4())
    advice_graph = create_advice_graph(enable_rag, session_id)

    initial_state: AdviceState = {
        "topic": topic,
        "messages": [],
        "prev_node": "START",  # 이전 노드 START로 설정
        "docs": {},  # RAG 결과 저장
    }

    langfuse_handler = CallbackHandler(session_id=session_id)

    # 스트리밍 응답 반환
    return StreamingResponse(
        advice_generator(advice_graph, initial_state, langfuse_handler),
        media_type="text/event-stream",
    )
