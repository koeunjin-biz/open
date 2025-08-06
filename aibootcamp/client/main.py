import json
import os
from dotenv import load_dotenv
import requests
import streamlit as st
from components.history import save_adviceitem
from components.sidebar import render_sidebar
from utils.state_manager import init_session_state, reset_session_state


class AgentType:
    IPO = "IPO_AGENT"
    

def process_event_data(event_data):
    print(f"[START]main.process_event_data({event_data.get("type")})")
    # 이벤트 종료
    if event_data.get("type") == "end":
        return True

    # 새로운 메세지
    if event_data.get("type") == "update":
        # state 추출
        data = event_data.get("data", {})

        role = data.get("role")
        response = data["response"]
        topic = data["topic"]
        messages = data["messages"]
        docs = data.get("docs", {})

        message = response

        avatar = "👩🏻‍⚖️"

        with st.chat_message(role, avatar=avatar):
            st.markdown(message)

        
        st.session_state.app_mode = "results"
        st.session_state.viewing_history = False
        st.session_state.messages = messages
        st.session_state.docs = docs

        # 완료된 토론 정보 저장
        save_adviceitem(
            topic,
            messages,
            docs,
        )

        # 참고 자료 표시
        if st.session_state.docs:
            render_source_materials()

        if st.button("새 토론 시작"):
            reset_session_state()
            st.session_state.app_mode = "input"
            st.rerun()

    return False


def process_streaming_response(response):
    print(f"[START]main.process_streaming_response({response})")
    
    for chunk in response.iter_lines():
        print(f"[START]main.process_streaming_response.chunk=[{chunk}]")

        if not chunk:
            continue

        # 'data: ' 접두사 제거
        line = chunk.decode("utf-8")
        print(f"[START]main.process_streaming_response.line=[{line}]")

        # line의 형태는 'data: {"type": "update", "data": {}}'
        if not line.startswith("data: "):
            continue

        data_str = line[6:]  # 'data: ' 부분 제거
        print(f"[START]main.process_streaming_response.data_str=[{data_str}]")


        try:
            # JSON 데이터 파싱
            event_data = json.loads(data_str)
            print(f"[START]main.process_streaming_response.event_data=[{event_data}]")

            # 이벤트 데이터 처리
            is_complete = process_event_data(event_data)
            print(f"[START]main.process_streaming_response.is_complete=[{is_complete}]")

            if is_complete:
                break

        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {e}")

    print(f"[END]process_streaming_response({response})")


def start_advice():
    print(f"[START]main.start_advice()")

    topic = st.session_state.ui_topic
    enabled_rag = st.session_state.get("ui_enable_rag", False)

    with st.spinner("상담이 진행 중입니다... 완료까지 잠시 기다려주세요."):
        # API 요청 데이터
        data = {
            "topic": topic,
            "enable_rag": enabled_rag,
        }

        # 포트 충돌 방지를 위해 환경변수 사용
        API_BASE_URL = os.getenv("API_BASE_URL")
        
        print(f"[START]main.start_advice.data=[{data}]")

        try:
            # 스트리밍 API 호출
            response = requests.post(
                f"{API_BASE_URL}/workflow/advice/stream",
                json=data,
                stream=True,
                headers={"Content-Type": "application/json"},
            )

            # stream=True로 설정하여 스트리밍 응답 처리
            # iter_lines() 또는 Iter_content()로 청크단위로 Read

            if response.status_code != 200:
                st.error(f"API 오류: {response.status_code} - {response.text}")
                return

            process_streaming_response(response)

        except requests.RequestException as e:
            st.error(f"API 요청 오류: {str(e)}")


# 참고 자료 표시
def render_source_materials():
    print(f"[START]main.render_source_materials()")
    with st.expander("사용된 참고 자료 보기"):
        st.subheader("참고 자료")
        for i, doc in enumerate(st.session_state.docs.get(AgentType.IPO, [])[:3]):
            st.markdown(f"**문서 {i+1}**")
            st.text(doc[:300] + "..." if len(doc) > 300 else doc)
            st.divider()


def display_advice_results():
    print(f"[START]main.display_advice_results()")
    if st.session_state.viewing_history:
        st.info("📚 이전에 저장된 상담내역을 보고 있습니다.")
        topic = st.session_state.loaded_topic
    else:
        topic = st.session_state.ui_topic

    # 상담내역 표시
    st.header(f"상담내역: {topic}")

    for message in st.session_state.messages:

        role = message["role"]
      
        if message["role"] == AgentType.IPO:
            avatar = "👩🏻‍⚖️"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    st.session_state.viewing_history = False

    # 참고 자료 표시
    if st.session_state.docs:
        render_source_materials()

    if st.button("새 상담 시작"):
        reset_session_state()
        st.session_state.app_mode = "input"
        st.rerun()


def render_ui():
    print(f"[START]main.render_ui()")

    # 페이지 설정
    st.set_page_config(page_title="IPO 상담", page_icon="🤖")

    # 제목 및 소개
    st.title("🤖 IPO 상담 - 에이전트")
    st.markdown(
        """
        ### 프로젝트 소개
        한국거래소에 상장하기위한 절차를 가이드해 드립니다.
        
        상장이란, 한국거래소가 정한 요건을 충족한 기업이 발행한 주권을 증권시장에서 거래할 수 있도록 허용하는 것입니다.
        """
    )

    #sidebar표시
    render_sidebar()

    #
    current_mode = st.session_state.app_mode
    print(f"[START]main.render_ui.current_mode=[{current_mode}]")
    if current_mode == "advice":
        start_advice()
    elif current_mode == "results":
        display_advice_results()


if __name__ == "__main__":

    load_dotenv()

    # 세션 상태 초기화
    init_session_state()

    render_ui()


# command
# streamlit run main.py