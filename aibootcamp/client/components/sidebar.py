import streamlit as st

from typing import Dict, Any

from components.history import render_history_ui


def render_input_form():
    with st.form("advice_form", border=False):
        # 상담내역 입력
        st.text_input(
            label="상담내역을 입력하세요:",
            value="주식시장에 상장신청하려고 하는데, 준비해야하는 서류가 무엇인가?",
            key="ui_topic",
        )

        st.form_submit_button(
            "상담 시작",
            on_click=lambda: st.session_state.update({"app_mode": "advice"}),
        )
        # RAG 기능 활성화 옵션
        st.checkbox(
            "RAG 활성화",
            value=True,
            help="외부 지식을 검색하여 토론에 활용합니다.",
            key="ui_enable_rag",
        )


def render_sidebar() -> Dict[str, Any]:
    with st.sidebar:

        tab1, tab2 = st.tabs(["새 상담", "상담 이력"])

        with tab1:
            render_input_form()

        with tab2:
            render_history_ui()
