from workflow.agents.con_agent import ConAgent
from workflow.agents.judge_agent import JudgeAgent
from workflow.agents.pro_agent import ProAgent
from workflow.agents.round_manager import RoundManager
from workflow.state import AdviceState, AgentType
from langgraph.graph import StateGraph, END


def create_advice_graph(enable_rag: bool = True, session_id: str = ""):

    # 그래프 생성
    workflow = StateGraph(AdviceState)

    # 에이전트 인스턴스 생성 - enable_rag에 따라 검색 문서 수 결정
    pro_agent = ProAgent(k=k_value, session_id=session_id)

    # 노드 추가
    workflow.add_node(AgentType.PRO, pro_agent.run)

    workflow.add_conditional_edges(
        "INCREMENT_ROUND",
        lambda s: (
            AgentType.JUDGE if s["current_round"] > s["max_rounds"] else AgentType.PRO
        ),
        [AgentType.JUDGE, AgentType.PRO],
    )

    workflow.set_entry_point(AgentType.PRO)
    workflow.add_edge(AgentType.JUDGE, END)

    # 그래프 컴파일
    return workflow.compile()


if __name__ == "__main__":

    graph = create_debate_graph(True)

    graph_image = graph.get_graph().draw_mermaid_png()

    output_path = "debate_graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)

    import subprocess

    subprocess.run(["open", output_path])
