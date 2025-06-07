

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from models import RewardPool


def add_reward_pool(db: Session,name:str):
    new_pool = RewardPool(name=name)
    db.add(new_pool)
    db.commit()
    db.refresh(new_pool)
    return new_pool.id

def remove_reward_pool(db: Session,pool_id:int):
    remove_pool = db.query(RewardPool).filter(RewardPool.id == pool_id).first()
    if remove_pool:
        db.delete(remove_pool)  # 這裡會啟動 cascade
        db.commit()
    return
