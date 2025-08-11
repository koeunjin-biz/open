"""
IPO 상담 클라이언트 메인 애플리케이션

이 모듈은 Streamlit 기반의 웹 인터페이스를 제공하여
KRX 상장 관련 상담을 받을 수 있는 클라이언트 애플리케이션입니다.

주요 기능:
- 실시간 스트리밍 상담
- 상담 내역 관리
- 참고 자료 표시
"""

import json
import os
from dotenv import load_dotenv
import requests
import streamlit as st
from components.history import save_adviceitem
from components.sidebar import render_sidebar
from utils.state_manager import init_session_state, reset_session_state


class AgentType:
    """에이전트 타입 정의"""
    IPO = "IPO_AGENT"  # KRX 상장심사 담당자 에이전트
    

def process_event_data(event_data):
    """
    서버에서 받은 이벤트 데이터를 처리합니다.
    
    Args:
        event_data (dict): 서버에서 전송된 이벤트 데이터
        
    Returns:
        bool: 이벤트 처리가 완료되었는지 여부
    """
    print(f"[START]main.process_event_data({event_data.get("type")})")
    
    # 이벤트 종료 처리
    if event_data.get("type") == "end":
        return True

    # 새로운 메시지 처리
    if event_data.get("type") == "update":
        # 이벤트 데이터에서 상태 정보 추출
        data = event_data.get("data", {})

        role = data.get("role")  # 에이전트 역할
        response = data["response"]  # 에이전트 응답
        topic = data["topic"]  # 상담 주제
        messages = data["messages"]  # 전체 대화 내역
        docs = data.get("docs", {})  # 참고 자료

        message = response

        # 에이전트 아바타 설정
        avatar = "👩🏻‍⚖️"  # KRX 상장심사 담당자

        # 채팅 메시지로 응답 표시
        with st.chat_message(role, avatar=avatar):
            st.markdown(message)

        # 세션 상태 업데이트
        st.session_state.app_mode = "results"  # 결과 모드로 전환
        st.session_state.viewing_history = False
        st.session_state.messages = messages
        st.session_state.docs = docs

        # 완료된 상담내역 정보를 데이터베이스에 저장
        save_adviceitem(
            topic,
            messages,
            docs,
        )

        # 참고 자료가 있으면 표시
        if st.session_state.docs:
            render_source_materials()

    return False


def process_streaming_response(response):
    """
    서버의 스트리밍 응답을 처리합니다.
    
    Server-Sent Events (SSE) 형식으로 전송되는 데이터를
    청크 단위로 받아서 처리합니다.
    
    Args:
        response: requests.Response 객체 (stream=True로 설정됨)
    """
    print(f"[START]main.process_streaming_response({response})")
    
    # 응답을 라인 단위로 처리
    for chunk in response.iter_lines():
        print(f"[START]main.process_streaming_response.chunk=[{chunk}]")

        # 빈 청크 무시
        if not chunk:
            continue

        # UTF-8로 디코딩
        line = chunk.decode("utf-8")
        print(f"[START]main.process_streaming_response.line=[{line}]")

        # SSE 형식 확인: 'data: {"type": "update", "data": {}}'
        if not line.startswith("data: "):
            continue

        # 'data: ' 접두사 제거하여 JSON 문자열 추출
        data_str = line[6:]
        print(f"[START]main.process_streaming_response.data_str=[{data_str}]")

        try:
            # JSON 문자열을 파이썬 객체로 파싱
            event_data = json.loads(data_str)
            print(f"[START]main.process_streaming_response.event_data=[{event_data}]")

            # 이벤트 데이터 처리
            is_complete = process_event_data(event_data)
            print(f"[START]main.process_streaming_response.is_complete=[{is_complete}]")

            # 상담이 완료되면 루프 종료
            if is_complete:
                break

        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {e}")

    print(f"[END]process_streaming_response({response})")


def start_advice():
    """
    상담을 시작하는 함수입니다.
    
    사용자 입력을 받아서 서버에 스트리밍 API 요청을 보내고,
    실시간으로 응답을 받아서 화면에 표시합니다.
    """
    print(f"[START]main.start_advice()")

    # 세션에서 사용자 입력 가져오기
    topic = st.session_state.ui_topic  # 상담 주제
    enabled_rag = st.session_state.get("ui_enable_rag", False)  # RAG 기능 활성화 여부

    # 로딩 스피너 표시
    with st.spinner("상담이 진행 중입니다... 완료까지 잠시 기다려주세요."):
        # 서버로 전송할 요청 데이터 구성
        data = {
            "topic": topic,
            "enable_rag": enabled_rag,
        }

        # 환경변수에서 API 기본 URL 가져오기
        API_BASE_URL = os.getenv("API_BASE_URL")
        
        print(f"[START]main.start_advice.data=[{data}]")

        try:
            # 스트리밍 API 호출 (실시간 응답을 위해 stream=True 설정)
            response = requests.post(
                f"{API_BASE_URL}/workflow/advice/stream",
                json=data,
                stream=True,  # 스트리밍 응답 활성화
                headers={"Content-Type": "application/json"},
            )

            # HTTP 상태 코드 확인
            if response.status_code != 200:
                st.error(f"API 오류: {response.status_code} - {response.text}")
                return

            # 스트리밍 응답 처리
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