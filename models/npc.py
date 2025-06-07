

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table,Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base


class NPC(Base):
    __tablename__ = "npcs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)

    # 不需要記錄 map_area_id，因為這是動態、個人化的


class UserNPCState(Base):
    __tablename__ = "user_npc_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    npc_id: Mapped[int] = mapped_column(ForeignKey("npcs.id"))

    # NPC 對該名使用者而言的所在區域
    map_area_id: Mapped[int] = mapped_column(ForeignKey("map_areas.id"))

    # 是否已互動、劇情進度、是否隱藏等等（可選欄位）
    has_talked: Mapped[bool] = mapped_column(default=False)
    is_visible: Mapped[bool] = mapped_column(default=True)

    npc: Mapped["NPC"] = relationship("NPC")
    user: Mapped["User"] = relationship("User") # type: ignore
    map_area: Mapped["MapArea"] = relationship("MapArea")  # type: ignore
