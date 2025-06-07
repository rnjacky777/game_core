from datetime import datetime
from sqlalchemy import JSON, Boolean, DateTime, Integer, String, ForeignKey,Column
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base


class User(Base):
    __tablename__ = "users"

    # Profile
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # Package
    money: Mapped[int] = mapped_column(default=0)
    current_map_id: Mapped[int] = mapped_column(ForeignKey("maps.id"), nullable=False, default=1)
    current_map = relationship("Map")  # 若你有 Map model 的話

    current_progress = relationship("UserMapProgress", uselist=False)
    # 一支隊伍的六個成員（或少於六個）
    team_members: Mapped[list["UserTeamMember"]] = relationship(
        "UserTeamMember", back_populates="user", cascade="all, delete-orphan"
    )

    # logging
    characters: Mapped[list["UserChar"]] = relationship(
        "UserChar", back_populates="owner")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, money={self.money})>"


class UserChar(Base):
    __tablename__ = "user_chars"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
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
    is_in_team: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否在隊伍中
    owner: Mapped["User"] = relationship("User", back_populates="characters")
    template: Mapped["CharTemp"] = relationship( # type: ignore
        "CharTemp", back_populates="user_chars")  # type: ignore

class UserTeamMember(Base):
    __tablename__ = "user_team_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_char_id: Mapped[int] = mapped_column(ForeignKey("user_chars.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 位置 0~5，代表第幾格

    user: Mapped["User"] = relationship("User", back_populates="team_members")
    user_char: Mapped["UserChar"] = relationship("UserChar")
