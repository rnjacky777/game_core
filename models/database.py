from __future__ import annotations
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,DeclarativeBase

DATABASE_URL = "sqlite:///./game_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

with engine.connect() as connection:
    connection.execute(text("PRAGMA foreign_keys = ON;"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
