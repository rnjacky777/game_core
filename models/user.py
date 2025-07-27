from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import JSON, Boolean, DateTime, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from core_system.models.database import Base

if TYPE_CHECKING:
    from core_system.models.maps import Map, MapArea, UserMapProgress
    from core_system.models.char_temp import CharTemp


class User(Base):
    __tablename__ = "users"

    # Profile
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # logging

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)
    user_data: Mapped["UserData"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    # def __repr__(self):
    #     return f"<User(id={self.id}, username={self.username}, money={self.money})>"


class UserChar(Base):
    __tablename__ = "user_chars"

    id: Mapped[int] = mapped_column(primary_key=True)
    char_temp_id: Mapped[int] = mapped_column(ForeignKey("char_temp.id"))

    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)
    hp: Mapped[int] = mapped_column(Integer)
    mp: Mapped[int] = mapped_column(Integer)
    atk: Mapped[int] = mapped_column(Integer)
    spd: Mapped[int] = mapped_column(Integer)
    def_: Mapped[int] = mapped_column(Integer)  # "def" 是 Python 關鍵字，避免使用

    status_effects: Mapped[dict] = mapped_column(JSON, default=dict)

    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)  # 防止被誤刪
    owner: Mapped["UserData"] = relationship(
        "UserData", back_populates="characters")
    user_data_id: Mapped[int] = mapped_column(
        ForeignKey("user_data.id"), nullable=False
    )
    template: Mapped["CharTemp"] = relationship(
        "CharTemp", back_populates="user_chars")


class UserTeamMember(Base):
    __tablename__ = "user_team_members"
    __table_args__ = (
        UniqueConstraint("user_data_id", "position", name="uq_user_position"),
        UniqueConstraint("user_data_id", "user_char_id", name="uq_user_char_in_team"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # 對應 UserData（使用者的遊戲資料）
    user_data_id: Mapped[int] = mapped_column(
        ForeignKey("user_data.id"), nullable=False)
    user_char_id: Mapped[int] = mapped_column(
        ForeignKey("user_chars.id"), nullable=False)

    # 隊伍位置，0~5
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # 關聯關係
    user_data: Mapped["UserData"] = relationship(back_populates="team_members")
    user_char: Mapped["UserChar"] = relationship()


class UserData(Base):
    __tablename__ = "user_data"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 關聯 User
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False)
    user: Mapped["User"] = relationship(back_populates="user_data")

    # 玩家基本資訊
    money: Mapped[int] = mapped_column(default=0)

    # 當前所在地圖
    current_map_id: Mapped[int] = mapped_column(
        ForeignKey("maps.id"), nullable=True)
    current_map: Mapped["Map"] = relationship()
    current_area_id: Mapped[int] = mapped_column(
        ForeignKey("map_areas.id"), nullable=True)
    current_area: Mapped["MapArea"] = relationship()

    map_progresses: Mapped[list["UserMapProgress"]] = relationship(
        back_populates="user_data",
        cascade="all, delete-orphan"
    )
    # 玩家隊伍成員（最多六位）
    team_members: Mapped[list["UserTeamMember"]] = relationship(
        back_populates="user_data",
        cascade="all, delete-orphan"
    )

    # 擁有的角色
    characters: Mapped[list["UserChar"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan"
    )
