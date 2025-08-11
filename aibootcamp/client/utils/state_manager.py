"""
Streamlit 세션 상태 관리

이 모듈은 Streamlit 애플리케이션의 세션 상태를 관리합니다.
사용자 상담 세션, 히스토리 조회, UI 상태 등을 추적합니다.
"""

import streamlit as st


def init_session_state():
    """
    애플리케이션 세션 상태를 초기화합니다.
    
    앱이 처음 실행될 때 호출되며, 필요한 세션 변수들을
    기본값으로 설정합니다.
    """
    # 세션 상태가 초기화되지 않은 경우에만 초기화
    if "app_mode" not in st.session_state:
        reset_session_state()


def reset_session_state():
    """
    세션 상태를 기본값으로 리셋합니다.
    
    새로운 상담을 시작할 때 호출되며,
    이전 상담의 모든 상태를 초기화합니다.
    """
    st.session_state.app_mode = False  # 앱 모드 (input/advice/results)
    st.session_state.viewing_history = False  # 히스토리 조회 중 여부
    st.session_state.loaded_adviceitem_id = None  # 로드된 상담 ID
    st.session_state.docs = {}  # 참고 자료


def set_advice_to_state(topic, messages, adviceitem_id, docs):
    """
    상담 데이터를 세션 상태에 설정합니다.
    
    히스토리에서 상담을 로드할 때 호출되며,
    선택된 상담의 정보를 세션에 저장합니다.
    
    Args:
        topic (str): 상담 주제
        messages (list): 대화 내역
        adviceitem_id (int): 상담 ID
        docs (dict): 참고 자료
    """
    st.session_state.app_mode = True  # 결과 모드로 설정
    st.session_state.messages = messages  # 대화 내역 저장
    st.session_state.viewing_history = True  # 히스토리 조회 모드
    st.session_state.adviceitem_topic = topic  # 상담 주제
    st.session_state.loaded_adviceitem_id = adviceitem_id  # 상담 ID
    st.session_state.docs = docs  # 참고 자료
