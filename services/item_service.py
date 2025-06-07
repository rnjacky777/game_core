

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from models import Item


def fetch_items(
    db: Session,
    item_type: Optional[str],
    started_id: Optional[int],
    limit: int,
    direction: str = "next"
):
    query = db.query(Item)

    if item_type:
        query = query.filter(Item.item_type == item_type)

    if started_id is not None:
        if direction == "next":
            query = query.filter(Item.id > started_id)
            query = query.order_by(Item.id.asc())
        else:
            query = query.filter(Item.id < started_id)
            query = query.order_by(Item.id.desc())
    else:
        query = query.order_by(Item.id.asc())

    items = query.limit(limit).all()

    # 若是 prev 模式要反轉順序，保持統一為 id 遞增
    if direction == "prev":
        items.reverse()

    return items


def get_item_by_id(db: Session, item_id: int) -> Item:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
