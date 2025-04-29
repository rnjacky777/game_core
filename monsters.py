from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from models.database import Base


class Monster(Base):
    __tablename__ = 'monsters'
    # Add more detail
    id = Column(Integer, primary_key=True)
    name = Column(String)
    drop_pool_id = Column(Integer, ForeignKey('reward_pools.id'))
    drop_pool = relationship("RewardPool", back_populates="monsters")


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
