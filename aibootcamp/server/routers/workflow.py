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
    topic: str
    enable_rag: bool = True


class WorkflowResponse(BaseModel):
    status: str = "success"
    result: Any = None


async def advice_generator(advice_graph, initial_state, langfuse_handler):
    print(f"[START]workflow.advice_generator({advice_graph},{initial_state},{langfuse_handler})")
    # 그래프에서 청크 스트리밍
    for chunk in advice_graph.stream(
        initial_state,
        config={"callbacks": [langfuse_handler]},
        subgraphs=True,
        stream_mode="updates",
    ):
        if not chunk:
            continue

        node = chunk[0] if len(chunk) > 0 else None
        if not node or node == ():
            continue

        node_name = node[0]
        role = node_name.split(":")[0]
        subgraph = chunk[1]
        subgraph_node = subgraph.get("update_state", None)

        if subgraph_node:
            response = subgraph_node.get("response", None)
            advice_state = subgraph_node.get("advice_state", None)
            messages = advice_state.get("messages", [])
            docs = advice_state.get("docs", {})
            topic = advice_state.get("topic")

            state = {
                "role": role,
                "response": response,
                "topic": topic,
                "messages": messages,
                "docs": docs,
            }

            event_data = {"type": "update", "data": state}
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            print(event_data)

            await asyncio.sleep(0.01)

    # 디베이트 종료 메시지
    yield f"data: {json.dumps({'type': 'end', 'data': {}}, ensure_ascii=False)}\n\n"


# 엔드포인트 경로 수정 (/advice/stream -> 유지)
@router.post("/advice/stream")
async def stream_advice_workflow(request: WorkflowRequest):
    print(f"[START]workflow.stream_advice_workflow({request})")

    topic = request.topic
    enable_rag = request.enable_rag

    print(f"topic=[{topic}]")
    print(f"enable_rag=[{enable_rag}]")

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
