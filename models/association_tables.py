from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Column, Integer, Float, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base
if TYPE_CHECKING:
    from core_system.models.maps import Map


class MapEventAssociation(Base):
    __tablename__ = "map_event_association"
    map_id: Mapped[int] = mapped_column(ForeignKey("maps.id"), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # 關聯
    event: Mapped["Event"] = relationship(back_populates="map_associations") # type: ignore
    map: Mapped["Map"] = relationship(back_populates="event_associations") # type: ignore


class MapAreaEventAssociation(Base):
    __tablename__ = "map_area_event_association"
    map_area_id: Mapped[int] = mapped_column(ForeignKey("map_areas.id"), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # 關聯
    event: Mapped["Event"] = relationship(back_populates="area_associations") # type: ignore
    area: Mapped["MapArea"] = relationship(back_populates="event_associations") # type: ignore


class MapConnection(Base):
    __tablename__ = "map_connections"
    __table_args__ = (
        UniqueConstraint("map_a_id", "map_b_id", name="uq_map_connection_pair"),
        CheckConstraint("map_a_id < map_b_id", name="chk_map_order"),  # 保證順序統一（A < B）
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    map_a_id: Mapped[int] = mapped_column(ForeignKey("maps.id"), nullable=False)
    map_b_id: Mapped[int] = mapped_column(ForeignKey("maps.id"), nullable=False)

    # 未來開啟條件欄位範例
    is_locked: Mapped[bool] = mapped_column(default=False)
    required_item: Mapped[str] = mapped_column(String(100), nullable=True)
    required_level: Mapped[int] = mapped_column(default=0)

    # 關聯回 Map
    map_a: Mapped["Map"] = relationship(
        "Map",
        foreign_keys=[map_a_id],
        back_populates="connections_a"
    )
    map_b: Mapped["Map"] = relationship(
        "Map",
        foreign_keys=[map_b_id],
        back_populates="connections_b"
    )