from workflow.agents.agent import Agent
from workflow.state import AgentType
from typing import Dict, Any


class IPOAgent(Agent):

    def __init__(self, k: int = 2, session_id: str = None):
        super().__init__(
            system_prompt="당신은 KRX에 상장심사 담당자입니다. KRX의 각종 시장에 상장하려고 하는 사람들에게 적극적으로 가이드를 해주어야 합니다.",
            role=AgentType.IPO,
            k=k,
            session_id=session_id,
        )

    def _create_prompt(self, state: Dict[str, Any]) -> str:
        print(f"[START]ipo_agent._create_prompt({self},{state})")
        return f"""
            당신은 '{state['topic']}'에 대해 KRX시장에 상장하는 방법을 가이드해주세요.
            2 ~ 3문단, 각 문단은 100자내로 작성해주세요.
            응답내용에 절차가 있다면, 도식화해서 제시하면 더 좋을 듯합니다.
            """
