

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from core_system.models import RewardPool
from core_system.models.items import RewardPoolItem


def add_reward_pool(db: Session, name: str):
    new_pool = RewardPool(name=name)
    db.add(new_pool)
    db.commit()
    db.refresh(new_pool)
    return new_pool.id


def remove_reward_pool(db: Session, pool_id: int):
    remove_pool = db.query(RewardPool).filter(RewardPool.id == pool_id).first()
    if remove_pool:
        db.delete(remove_pool)  # 這裡會啟動 cascade
        db.commit()
    return


def add_reward_pool_item(db: Session, pool_id: int, item_id: int, probability: float = 0):
    reward_pool_item = RewardPoolItem(
        pool_id=pool_id,
        item_id=item_id,
        probability=probability
    )
    db.add(reward_pool_item)
    db.commit()
    return


def remove_reward_pool_item(db: Session, pool_id: int, item_id: int):
    remove_pool_item = db.query(RewardPoolItem).filter(RewardPoolItem.pool_id == pool_id and RewardPoolItem.item_id==item_id).first()
    db.delete(remove_pool_item)
    db.commit()
    return
