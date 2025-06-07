from sqlalchemy import Column, Integer, String
from core_system.models.database import Base


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String, nullable=False)
