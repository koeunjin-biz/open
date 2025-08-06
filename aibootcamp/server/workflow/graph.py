from workflow.agents.ipo_agent import IPOAgent
from workflow.state import AdviceState, AgentType
from langgraph.graph import StateGraph, END


def create_advice_graph(enable_rag: bool = True, session_id: str = ""):

    # 그래프 생성
    workflow = StateGraph(AdviceState)

    # 에이전트 인스턴스 생성 - enable_rag에 따라 검색 문서 수 결정
    ipo_agent = IPOAgent(session_id=session_id)

    # 노드 추가
    workflow.add_node(AgentType.IPO, ipo_agent.run)
    workflow.set_entry_point(AgentType.IPO)
    workflow.add_edge(AgentType.IPO, END)

    # 그래프 컴파일
    return workflow.compile()


if __name__ == "__main__":

    graph = create_advice_graph(True)

    graph_image = graph.get_graph().draw_mermaid_png()

    output_path = "advice_graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)

    import subprocess

    subprocess.run(["open", output_path])
