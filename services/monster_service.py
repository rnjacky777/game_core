

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from core_system.models import Monster


def fetch_monsters(
    db: Session,
    started_id: Optional[int],
    limit: int,
    direction: str = "next"
):
    query = db.query(Monster)

    if started_id is not None:
        if direction == "next":
            query = query.filter(Monster.id > started_id)
            query = query.order_by(Monster.id.asc())
        else:
            query = query.filter(Monster.id < started_id)
            query = query.order_by(Monster.id.desc())
    else:
        query = query.order_by(Monster.id.asc())

    monsters = query.limit(limit).all()

    if direction == "prev":
        monsters.reverse()

    return monsters


def get_monster_by_id(db: Session, monster_id: int) -> Monster:
    monster = db.query(Monster).filter(Monster.id == monster_id).first()
    if not monster:
        raise HTTPException(status_code=404, detail="Monster not found")
    return monster
