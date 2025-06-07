from __future__ import annotations
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    # 'equipment', 'consumable', 'quest',"material" 雜項
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Common
    price: Mapped[int] = mapped_column(Integer, default=0)
    rarity: Mapped[int] = mapped_column(Integer, default=1)

    # 裝備專屬欄位（選填）
    # 'weapon', 'armor', etc.
    slot: Mapped[str] = mapped_column(String(20), nullable=True)
    atk_bonus: Mapped[int] = mapped_column(Integer, nullable=True)
    def_bonus: Mapped[int] = mapped_column(Integer, nullable=True)

    # 消耗品專屬欄位（選填）
    hp_restore: Mapped[int] = mapped_column(Integer, nullable=True)
    mp_restore: Mapped[int] = mapped_column(Integer, nullable=True)

    # 任務道具也可加 quest_id（選填）
    related_quest: Mapped[int] = mapped_column(Integer, nullable=True)


class RewardPoolItem(Base):
    __tablename__ = 'reward_pool_items'
    id = Column(Integer, primary_key=True)

    pool_id = Column(Integer, ForeignKey('reward_pools.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    probability = Column(Float, nullable=False)  # 0.0 ~ 1.0

    pool = relationship("RewardPool", back_populates="items")
    item_detail:Mapped["Item"] = relationship("Item")

