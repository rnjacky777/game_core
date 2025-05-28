from __future__ import annotations
import json
from typing import TYPE_CHECKING, List
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.database import Base

if TYPE_CHECKING:
    from models import RewardPoolItem


'''
Event logic
Event pool -> Get event 
Check event type
Battle event -> pick up monster -> battle -> win -> Get reward(monster)
                                          -> lost -> Show lose phote nothing happend
General
'''


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    # "battle", "normal", "special"
    type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)

    maps = relationship(  # type: ignore
        "Map",
        secondary="map_event_association",
        back_populates="events"
    )
    areas = relationship(
        "MapArea",  # <- 注意這裡是字串
        secondary="map_area_event_association",
        back_populates="events"
    )
    # 其他欄位如事件劇情、條件、結果等在這邊擴充


class EventResult(Base):
    __tablename__ = 'event_results'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, server_default=text("No name"))
    reward_pool_id = Column(Integer, ForeignKey('reward_pools.id'))
    # e.g., {"poison": 3, "heal": 100}
    status_effects_json = Column(Text, nullable=True)
    story_text = Column(Text)
    reward_pool = relationship("RewardPool", back_populates="event_results")

    def get_story_text(self) -> list[StoryTextData]:
        return [StoryTextData(**item) for item in json.loads(self.story_text)]

    def set_story_text(self, data: list[StoryTextData]):
        self.story_text = json.dumps([item.model_dump() for item in data])


class RewardPool(Base):
    __tablename__ = 'reward_pools'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)

    # 關聯到 pool_items
    items: Mapped[List["RewardPoolItem"]] = relationship(  # type: ignore
        "RewardPoolItem", back_populates="pool", cascade="all, delete-orphan")
    monsters = relationship(
        "Monster", back_populates="drop_pool")  # 哪些怪物使用這個 pool
    event_results = relationship(
        "EventResult", back_populates="reward_pool")  # 哪些事件結果使用這個 pool


class GeneralEventLogic(Base):
    __tablename__ = 'general_event_logic'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    story_text = Column(Text)  # 可為 JSON 字串，支援多段落
    condition_json = Column(Text)  # TODO 未來補上 儲存條件，例如 {"has_item": "torch"}

    event = relationship("Event", backref="general_logic")

    def get_condition_list(self) -> list[ConditionData]:
        return [ConditionData(**item) for item in json.loads(self.story_text)]

    def set_condition_list(self, data: list[ConditionData]):
        self.condition_json = json.dumps([item.model_dump() for item in data])

    def get_story_text(self) -> list[StoryTextData]:
        return [StoryTextData(**item) for item in json.loads(self.story_text)]

    def set_story_text(self, data: list[StoryTextData]):
        self.story_text = json.dumps([item.model_dump() for item in data])


class ConditionData(BaseModel):
    result_id: int
    condition: list[dict] = []
    prior: int


class StoryTextData(BaseModel):
    name: str = None
    text: str


class BattleEventLogic(Base):
    __tablename__ = 'battle_event_logic'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    story_text = Column(Text)
    monster_pool_id = Column(Integer, ForeignKey('monster_pools.id'))
    reward_pool_id = Column(Integer, ForeignKey('reward_pools.id'))

    event = relationship("Event", backref="battle_logic")
