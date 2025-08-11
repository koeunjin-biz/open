import uvicorn
from fastapi import FastAPI

# 절대 경로 임포트로 수정
from routers import history
from routers import workflow
from utils.config import save_vectorstore

# 데이터베이스 초기화를 위한 임포트 추가
from db.database import Base, engine

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

# FastAPI 인스턴스 생성
app = FastAPI(
    title="IPO Advisory Consultant API",
    description="IPO Advisory Consultant 서비스를 위한 API",
    version="0.1.0",
)

# router 추가
app.include_router(history.router)
app.include_router(workflow.router)

# 벡터 스토어 초기화 (여러 PDF 파일 처리)
import os
import shutil
from utils.config import save_multiple_pdfs_vectorstore

vector_index_path = "./vector_index"

# 기존 벡터 인덱스 삭제
if os.path.exists(vector_index_path):
    print("기존 벡터 인덱스 삭제 중...")
    shutil.rmtree(vector_index_path)
    print("기존 벡터 인덱스 삭제 완료")

print("여러 PDF 파일로 새로운 벡터 스토어 생성 중...")
try:
    vectorstore = save_multiple_pdfs_vectorstore("./data")
    if vectorstore:
        print("벡터 스토어 생성 완료")
    else:
        print("벡터 스토어 생성 실패")
except Exception as e:
    print(f"벡터 스토어 생성 실패: {e}")
    print("서버는 계속 실행되지만 검색 기능이 제한될 수 있습니다.")


# 실행은 server 경로에서
# . venv/bin/activate
# uvicorn main:app --port=8081
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)