from sqlalchemy import String, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core_system.models.database import Base
from core_system.models.user import UserChar


class CharTemp(Base):
    __tablename__ = "char_temp"

    # Profile
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    rarity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 ~ 6 星
    description: Mapped[str] = mapped_column(
        String(255), nullable=True)  # 顯示用介紹

    # Base status
    base_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    base_mp: Mapped[int] = mapped_column(Integer, nullable=False)
    base_atk: Mapped[int] = mapped_column(Integer, nullable=False)
    base_spd: Mapped[int] = mapped_column(Integer, nullable=False)
    base_def: Mapped[int] = mapped_column(Integer, nullable=False)

    # addtion
    user_chars: Mapped[list["UserChar"]] = relationship(
        "UserChar", back_populates="template")

    # implement skill
    # role: Mapped[str] = mapped_column(String(20), nullable=True)  # 例如：坦克、輸出、輔助
    # job: Mapped[str] = mapped_column(String(20), nullable=True)   # 例如：戰士、法師、弓手
    # skill_ids: Mapped[str] = mapped_column(String, nullable=True)  # JSON 字串格式技能 ID，或可改為關聯表
