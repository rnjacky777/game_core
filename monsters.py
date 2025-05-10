from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.database import Base

if TYPE_CHECKING:
    from models.event import RewardPool


class Monster(Base):
    __tablename__ = 'monsters'
    # Add more detail
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # attribute
    hp = Column(Integer, nullable=False, default=1)
    mp = Column(Integer, nullable=False, default=1)
    atk = Column(Integer, nullable=False, default=1)
    spd = Column(Integer, nullable=False, default=1)
    def_ = Column(Integer, nullable=False, default=1)

    # Connect to RewardPool
    drop_pool_id = Column(Integer, ForeignKey(
        'reward_pools.id'), nullable=True)
    drop_pool: Mapped[Optional["RewardPool"]] = relationship(
        "RewardPool", back_populates="monsters")  # type: ignore


class MonsterPool(Base):
    __tablename__ = 'monster_pools'
    id = Column(Integer, primary_key=True)
    name = Column(String)


class MonsterPoolEntry(Base):
    # == reward_pool_items Use this class to link monster and MonsterPool to countrol monster probability
    __tablename__ = 'monster_pool_entries'
    id = Column(Integer, primary_key=True)
    pool_id = Column(Integer, ForeignKey('monster_pools.id'))
    monster_id = Column(Integer, ForeignKey('monsters.id'))
    probability = Column(Float)

    monster = relationship("Monster")
    pool = relationship("MonsterPool", backref="entries")
