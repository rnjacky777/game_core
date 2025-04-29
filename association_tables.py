from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base
map_area_event_association = Table(
    "map_area_event_association",
    Base.metadata,
    Column("map_area_id", ForeignKey("map_areas.id"), primary_key=True),
    Column("event_id", ForeignKey("events.id"), primary_key=True),
)
# 關聯表：地圖與事件的多對多關聯
map_event_association = Table(
    "map_event_association",
    Base.metadata,
    Column("map_id", ForeignKey("maps.id"), primary_key=True),
    Column("event_id", ForeignKey("events.id"), primary_key=True)
)
map_connection = Table(
    "map_connection",
    Base.metadata,
    Column("from_map_id", ForeignKey("maps.id"), primary_key=True),
    Column("to_map_id", ForeignKey("maps.id"), primary_key=True)
)