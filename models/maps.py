# app/models/map.py

from typing import TYPE_CHECKING
from sqlalchemy import (JSON, Column, ForeignKey, Integer, String, Table, Text)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base
from core_system.models.user import UserData
# 多地圖連結
if TYPE_CHECKING:
    from .association_tables import MapConnection, MapEventAssociation
    # The following are defined later in this file, but this helps type checkers
    from . import MapArea, UserMapProgress

class Map(Base):
    __tablename__ = "maps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)

    # 透過關聯物件與 Event 建立關聯
    event_associations: Mapped[list["MapEventAssociation"]] = relationship(
        "MapEventAssociation", back_populates="map", cascade="all, delete-orphan"
    )

    # 每個 map 會有多個使用者進度
    user_progresses: Mapped[list["UserMapProgress"]] = relationship(
        "UserMapProgress",
        back_populates="map"
    )

    # 小地圖
    areas: Mapped[list["MapArea"]] = relationship(
        "MapArea", back_populates="map"
    )

    # 與 MapConnection 的雙向關聯（無方向連線）
    connections_a: Mapped[list["MapConnection"]] = relationship(
        "MapConnection",
        foreign_keys="[MapConnection.map_a_id]",
        back_populates="map_a",
        cascade="all, delete-orphan"
    )
    connections_b: Mapped[list["MapConnection"]] = relationship(
        "MapConnection",
        foreign_keys="[MapConnection.map_b_id]",
        back_populates="map_b",
        cascade="all, delete-orphan"
    )

    @property
    def neighbors(self) -> list["Map"]:
        """所有相鄰（雙向）且不論順序的地圖"""
        out = [conn.map_b for conn in self.connections_a]
        inc = [conn.map_a for conn in self.connections_b]
        return out + inc

    def get_unlocked_neighbors(self) -> list["Map"]:
        """過濾掉鎖住的連線後的鄰居"""
        out = [conn.map_b for conn in self.connections_a if not conn.is_locked]
        inc = [conn.map_a for conn in self.connections_b if not conn.is_locked]
        return out + inc

    def __repr__(self) -> str:
        return f"<Map(id={self.id}, name='{self.name}')>"
# app/models/map.py (繼續加在同一個檔案裡)


class UserMapProgress(Base):
    __tablename__ = "user_map_progress"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_data_id: Mapped[int] = mapped_column(ForeignKey("user_data.id"))
    map_id: Mapped[int] = mapped_column(ForeignKey("maps.id"))

    # 進度數值可以是百分比、已完成事件數等
    progress: Mapped[int] = mapped_column(default=0)
    is_completed: Mapped[bool] = mapped_column(default=False)

    # 關聯
    user_data: Mapped["UserData"] = relationship(back_populates="map_progresses")
    map: Mapped["Map"] = relationship("Map", back_populates="user_progresses")


class MapArea(Base):
    __tablename__ = "map_areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    map_id = Column(Integer, ForeignKey("maps.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)

    # 關聯 Map 和 Event
    map = relationship("Map", back_populates="areas")
    # 透過關聯物件與 Event 建立關聯
    event_associations: Mapped[list["MapAreaEventAssociation"]] = relationship( # type: ignore
        "MapAreaEventAssociation", back_populates="area", cascade="all, delete-orphan"
    )

    # 儲存初始 NPC 資料，若未來有變動或需要擴展，可以改為關聯到 NPC 表
    # [
    #     {"npc_id": 1, "npc_name": "森林守衛", "npc_role": "守護者"},
    #     {"npc_id": 2, "npc_name": "魔法商人", "npc_role": "商人"}
    # ]
    init_npc = Column(JSON, nullable=True)  # 存放區域的初始 NPC 資訊

    def __repr__(self):
        return f"<MapArea(id={self.id}, name={self.name}, map_id={self.map_id})>"