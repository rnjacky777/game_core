from __future__ import annotations
import json
from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base

if TYPE_CHECKING:
    from core_system.models import RewardPoolItem
    from association_tables import MapEventAssociation, MapAreaEventAssociation



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

    map_associations: Mapped[list["MapEventAssociation"]] = relationship(
        "MapEventAssociation", back_populates="event", cascade="all, delete-orphan"
    )

    area_associations: Mapped[list["MapAreaEventAssociation"]] = relationship( 
        "MapAreaEventAssociation", back_populates="event", cascade="all, delete-orphan"
    )
    # typing
    general_logic: Mapped[Optional["GeneralEventLogic"]] = relationship(
        "GeneralEventLogic", back_populates="event", uselist=False,
        cascade="all, delete-orphan"
    )
    # 其他欄位如事件劇情、條件、結果等在這邊擴充


class EventResult(Base):
    __tablename__ = 'event_results'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, default=text("No name"))

    condition_json = Column(Text, nullable=True, default="[]")
    prior = Column(Integer, nullable=True, default=0)
    # e.g., {"poison": 3, "heal": 100}
    status_effects_json = Column(Text, nullable=True, default="[]")
    story_text = Column(Text, nullable=True, default="[]")

    reward_pool_id = Column(Integer, ForeignKey('reward_pools.id'))
    reward_pool: Mapped["RewardPool"] = relationship(
        "RewardPool",
        back_populates="event_results",
        # foreign_keys=[reward_pool_id],
        cascade="all, delete-orphan",
        single_parent=True
    )

    general_event_logic_id = Column(
        Integer,
        ForeignKey('general_event_logic.id', ondelete="CASCADE"),
        nullable=True
    )
    general_event_logic = relationship("GeneralEventLogic",
                                       back_populates="event_results")

    def get_story_text(self) -> list[StoryTextData]:
        return [StoryTextData(**item) for item in json.loads(self.story_text)]

    def set_story_text(self, data: list[StoryTextData]):
        self.story_text = json.dumps([item.model_dump() for item in data])

    def get_condition_list(self) -> List[ConditionData]:
        return [ConditionData(**condition) for condition in json.loads(self.condition_json)]

    def set_condition_list(self, data: List[ConditionData]):
        self.condition_json = json.dumps(
            [condition.model_dump() for condition in data])

    def get_status_effects_json(self) -> List[StatusEffectData]:
        return [StatusEffectData(**status_effect) for status_effect in json.loads(self.status_effects_json)]

    def set_status_effects_json(self, data: List[StatusEffectData]):
        self.status_effects_json = json.dumps(
            [status.model_dump() for status in data])


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
    event_id = Column(Integer, ForeignKey(
        'events.id', ondelete="CASCADE"), unique=True)
    story_text = Column(Text, default="[]")  # 可為 JSON 字串，支援多段落
    # TODO 未來補上 儲存條件，例如 {"has_item": "torch"}

    event: Mapped["Event"] = relationship(
        "Event",
        uselist=False,
        back_populates="general_logic"
    )
    event_results: Mapped[List["EventResult"]] = relationship("EventResult",
                                                              back_populates="general_event_logic",
                                                              cascade="all, delete-orphan")

    def get_story_text(self) -> list[StoryTextData]:
        return [StoryTextData(**item) for item in json.loads(self.story_text)]

    def set_story_text(self, data: list[StoryTextData]):
        self.story_text = json.dumps([item.model_dump() for item in data])


class StoryTextData(BaseModel):
    name: Optional[str] = None
    text: str


class ConditionData(BaseModel):
    condition_key: Optional[str] = None
    condition_value: Optional[str] = None


class StatusEffectData(BaseModel):
    status_effect_key: Optional[str] = None
    status_effect_value: Optional[str] = None


class BattleEventLogic(Base):
    __tablename__ = 'battle_event_logic'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    story_text = Column(Text)
    monster_pool_id = Column(Integer, ForeignKey('monster_pools.id'))
    reward_pool_id = Column(Integer, ForeignKey('reward_pools.id'))

    event = relationship("Event", backref="battle_logic")
