import uvicorn
from fastapi import FastAPI

# 절대 경로 임포트로 수정
from routers import workflow
from routers import history
from utils.config import model_config

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

# 실행은 server 경로에서
# . venv/bin/activate
# uvicorn main:app --port=8001
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=model_config.PORT)