from sqlalchemy import Column, Integer, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base


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


# 保持 map_connection 不變
map_connection = Table(
    "map_connection",
    Base.metadata,
    Column("from_map_id", ForeignKey("maps.id"), primary_key=True),
    Column("to_map_id", ForeignKey("maps.id"), primary_key=True)
)