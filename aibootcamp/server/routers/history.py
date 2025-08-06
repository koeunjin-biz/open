from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from db.models import AdviceItem       
from db.schemas import AdviceItemSchema, AdviceItemCreate


router = APIRouter(prefix="/api/v1", tags=["history"])


# 상담내역 목록 조회
@router.get("/history/", response_model=List[AdviceItemSchema])
def read_adviceItems(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    print(f"[START]history.read_adviceItems({skip},{limit},{db})")

    adviceitems = db.query(AdviceItem).offset(skip).limit(limit).all()
    return adviceitems


# 상담내역 생성
@router.post("/history/", response_model=AdviceItemSchema)
def create_adviceItem(advice: AdviceItemCreate, db: Session = Depends(get_db)):
    print(f"[START]history.create_adviceItem({advice},{db})")

    db_advice = AdviceItem(**advice.model_dump())
    db.add(db_advice)
    db.commit()
    db.refresh(db_advice)
    return db_advice


# 상담내역 조회
@router.get("/history/{advice_id}", response_model=AdviceItemSchema)
def read_adviceitem(advice_id: int, db: Session = Depends(get_db)):
    print(f"[START]history.read_adviceitem({advice_id},{db})")

    db_advice = db.query(AdviceItem).filter(AdviceItem.id == advice_id).first()
    if db_advice is None:
        raise HTTPException(status_code=404, detail="AdviceItem not found")
    return db_advice


# 상담내역 삭제
@router.delete("/history/{advice_id}")
def delete_debate(advice_id: int, db: Session = Depends(get_db)):
    print(f"[START]history.delete_debate({advice_id},{db})")
    db_advice = db.query(AdviceItem).filter(AdviceItem.id == advice_id).first()
    if db_advice is None:
        raise HTTPException(status_code=404, detail="AdviceItem not found")

    db.delete(db_advice)
    db.commit()
    return {"detail": "AdviceItem successfully deleted"}
