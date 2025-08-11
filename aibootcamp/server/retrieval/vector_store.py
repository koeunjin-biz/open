#import streamlit as st
from typing import Any, Dict, List



def search_topic(topic: str, role: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
    print(f"[START]vector_store.search_topic({topic},{role},{query},{k})")
    
    try:
        # 기존 로컬 벡터 스토어 사용 (새로 생성하지 않음)
        from utils.config import load_vectorstore
        
        vector_store = load_vectorstore()
        if not vector_store:
            print("로컬 벡터 스토어 로드 실패")
            return []
        
        # 벡터 스토어에서 Similarity Search 수행
        return vector_store.similarity_search(query, k=k)
        
    except Exception as e:
        print(f"검색 중 오류 발생: {str(e)}")
        return []
