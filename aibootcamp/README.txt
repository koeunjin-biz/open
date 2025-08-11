================================================================================
                    IPO 상담 시스템 (IPO Advisory Consultant)
================================================================================

📋 프로젝트 개요
================================================================================
이 프로젝트는 한국거래소(KRX) 상장 관련 상담을 제공하는 AI 기반 웹 애플리케이션입니다.
LangGraph와 LangChain을 활용한 AI 에이전트가 사용자의 상장 관련 질문에 대해
실시간으로 답변을 제공하며, KRX 공식 가이드북을 기반으로 한 정확한 정보를 제공합니다.

🎯 주요 기능
================================================================================
• 실시간 AI 상담: KRX 상장심사 담당자 역할의 AI 에이전트
• 스트리밍 응답: Server-Sent Events를 통한 실시간 응답
• RAG 기반 검색: PDF 문서 기반 지식 검색 및 외부 검색 연동
• 상담 내역 관리: SQLite 데이터베이스를 통한 상담 기록 저장/조회
• 다중 PDF 처리: 4개 KRX 가이드북 통합 처리
• 웹 인터페이스: Streamlit 기반 사용자 친화적 UI

🏗️ 시스템 아키텍처
================================================================================
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   Server        │    │   AI Workflow   │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (LangGraph)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Session       │    │   SQLite DB     │    │   Vector Store  │
│   Management    │    │   (History)     │    │   (FAISS)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘

📁 프로젝트 구조
================================================================================
aibootcamp/
├── client/                          # 클라이언트 애플리케이션
│   ├── main.py                     # Streamlit 메인 앱
│   ├── components/                  # UI 컴포넌트
│   │   ├── history.py              # 상담 내역 관리
│   │   └── sidebar.py              # 사이드바 UI
│   └── utils/
│       └── state_manager.py        # 세션 상태 관리
├── server/                          # 서버 애플리케이션
│   ├── main.py                     # FastAPI 메인 서버
│   ├── routers/                    # API 라우터
│   │   ├── workflow.py             # 워크플로우 API
│   │   └── history.py              # 히스토리 API
│   ├── workflow/                   # AI 워크플로우
│   │   ├── agents/                 # AI 에이전트
│   │   │   ├── agent.py            # 기본 에이전트 클래스
│   │   │   └── ipo_agent.py        # IPO 상담 에이전트
│   │   ├── graph.py                # LangGraph 워크플로우
│   │   └── state.py                # 상태 정의
│   ├── retrieval/                  # 검색 시스템
│   │   ├── search_service.py       # 검색 서비스
│   │   └── vector_store.py         # 벡터 스토어 관리
│   ├── db/                         # 데이터베이스
│   │   ├── database.py             # DB 연결 설정
│   │   ├── models.py               # 데이터 모델
│   │   └── schemas.py              # Pydantic 스키마
│   ├── utils/                      # 유틸리티
│   │   └── config.py               # 설정 관리
│   ├── data/                       # PDF 문서
│   │   ├── [KRX+2024-07]+채권시장+상장공시+업무+가이드(2024년+개정판).pdf
│   │   ├── 2022년도+코넥스시장+상장업무+가이드(최종).pdf
│   │   ├── 2025_코스닥_상장심사_이해와_실무.pdf
│   │   └── 2024년+유가증권시장+상장심사+가이드북.pdf
│   ├── vector_index/               # 벡터 인덱스 (자동 생성)
│   └── history.db                  # SQLite 데이터베이스
└── requirements.txt                # Python 의존성

🚀 설치 및 실행
================================================================================

1. 환경 설정
   ```bash
   # Python 3.8+ 설치 필요
   python --version
   
   # 가상환경 생성 및 활성화
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

3. 환경변수 설정 (.env 파일 생성)
   ```bash
   # Azure OpenAI 설정
   AOAI_API_KEY=your_azure_openai_api_key
   AOAI_ENDPOINT=your_azure_openai_endpoint
   AOAI_DEPLOY_GPT4O=your_gpt4o_deployment_name
   AOAI_EMBEDDING_DEPLOYMENT=your_embedding_deployment_name
   AOAI_API_VERSION=2024-02-15-preview
   
   # Langfuse 설정 (모니터링)
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_HOST=https://cloud.langfuse.com
   
   # API 설정
   API_BASE_URL=http://localhost:8081
   ```

4. 서버 실행
   ```bash
   cd server
   uvicorn main:app --port=8081 --reload
   ```

5. 클라이언트 실행
   ```bash
   cd client
   streamlit run main.py
   ```

6. 웹 브라우저에서 접속
   ```
   http://localhost:8501
   ```

🔧 주요 기술 스택
================================================================================
• Frontend: Streamlit (Python 웹 프레임워크)
• Backend: FastAPI (Python API 프레임워크)
• AI/ML: LangChain, LangGraph, OpenAI GPT-4
• Database: SQLite (상담 내역), FAISS (벡터 검색)
• Document Processing: PyMuPDF, pdfplumber
• Monitoring: Langfuse
• Search: DuckDuckGo API, Wikipedia API

📚 사용된 KRX 가이드북
================================================================================
1. 채권시장 상장공시 업무 가이드 (2024년 개정판)
2. 코넥스시장 상장업무 가이드 (2022년도)
3. 코스닥 상장심사 이해와 실무 (2025년)
4. 유가증권시장 상장심사 가이드북 (2024년)

🎮 사용 방법
================================================================================
1. 웹 브라우저에서 애플리케이션 접속
2. "새 상담" 탭에서 상담 주제 입력
   예시: "채권상장하고 싶은데, 채권상장 절차를 알려주세요."
3. "RAG 활성화" 체크박스로 외부 검색 기능 선택
4. "상담 시작" 버튼 클릭
5. AI 에이전트의 실시간 응답 확인
6. "상담 이력" 탭에서 이전 상담 내역 조회

🔍 검색 시스템
================================================================================
• 1단계: 로컬 PDF 문서 검색 (우선)
• 2단계: 외부 검색 (DuckDuckGo + Wikipedia)
• 3단계: 기본 정보 제공 (검색 결과 없을 때)

📊 API 엔드포인트
================================================================================
• POST /api/v1/workflow/advice/stream - 스트리밍 상담
• GET /api/v1/history/ - 상담 내역 조회
• POST /api/v1/history/ - 상담 내역 저장
• GET /api/v1/history/{id} - 특정 상담 조회
• DELETE /api/v1/history/{id} - 상담 내역 삭제

🐛 문제 해결
================================================================================
1. 벡터 스토어 생성 오류
   - server/vector_index 폴더 삭제 후 서버 재시작
   - PDF 파일 경로 확인

2. API 연결 오류
   - .env 파일의 API_BASE_URL 확인
   - 서버가 8081 포트에서 실행 중인지 확인

3. Azure OpenAI 오류
   - API 키와 엔드포인트 설정 확인
   - 배포 이름이 올바른지 확인

4. Rate Limit 오류
   - 외부 검색 API 사용량 제한으로 인한 오류
   - 로컬 PDF 검색으로 자동 전환됨

📝 개발자 정보
================================================================================
• 프로젝트명: IPO Advisory Consultant
• 버전: 1.0.0
• 개발 언어: Python 3.8+
• 라이선스: MIT License

🔗 관련 링크
================================================================================
• 한국거래소(KRX): https://www.krx.co.kr
• LangChain: https://langchain.com
• LangGraph: https://langchain.com/langgraph
• Streamlit: https://streamlit.io
• FastAPI: https://fastapi.tiangolo.com

================================================================================
                           END OF README
================================================================================ 