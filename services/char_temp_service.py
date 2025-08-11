import logging
from typing import List, Literal, Optional

from sqlalchemy.orm import Session

from core_system.models import CharTemp
from schemas.char_temp import CharTempCreate


def create_char_temp(db: Session, char_data: CharTempCreate) -> CharTemp:
    """
    建立一個新的角色模板實例並將其加入到 session 中。

    此函式不會提交 transaction。

    Args:
        db (Session): 資料庫 session。
        char_data (CharTempCreate): 包含新角色模板資料的 Pydantic schema。

    Returns:
        CharTemp: 新建立的 SQLAlchemy CharTemp 物件。
    """
    char = CharTemp(**char_data.model_dump())
    db.add(char)
    return char


def fetch_char_temps(
    db: Session,
    started_id: Optional[int],
    limit: int,
    direction: Literal["next", "prev"] = "next",
    id: Optional[int] = None,
    name: Optional[str] = None,
) -> List[CharTemp]:
    """
    獲取角色模板列表，支援 ID 精確搜尋、名稱模糊搜尋以及 cursor-based 分頁。

    篩選條件的優先級為：ID 精確搜尋 > 名稱模糊搜尋。
    分頁邏輯僅在非 ID 精確搜尋時生效。

    Args:
        db (Session): 資料庫 session。
        started_id (Optional[int]): 分頁的起始 cursor ID。
        limit (int): 要獲取的最大項目數量。
        direction (Literal["next", "prev"]): 分頁方向。
        id (Optional[int]): 用於精確搜尋的角色模板 ID。
        name (Optional[str]): 用於模糊搜尋的角色模板名稱。

    Returns:
        List[CharTemp]: 符合條件的角色模板物件列表，一律以 ID 升序排列。
    """
    logging.debug(f"Fetching char temps: id={id}, name={name}, cursor={started_id}, limit={limit}, direction='{direction}'")
    query = db.query(CharTemp)

    # 若有指定 id，直接精確搜尋，不用分頁或模糊搜尋
    if id is not None:
        query = query.filter(CharTemp.id == id).order_by(CharTemp.id.asc())
        results = query.limit(limit).all()
        return results

    # 沒有 id，依 name 篩選（若有）
    if name:
        query = query.filter(CharTemp.name.ilike(f"%{name}%"))

    # 分頁條件
    if started_id is not None:
        if direction == "next":
            query = query.filter(CharTemp.id > started_id)
            query = query.order_by(CharTemp.id.asc())
        else:  # direction == "prev"
            query = query.filter(CharTemp.id < started_id)
            query = query.order_by(CharTemp.id.desc())
    else:
        query = query.order_by(CharTemp.id.asc())

    results = query.limit(limit).all()

    if direction == "prev":
        results.reverse()

    if results:
        logging.debug(f"Found {len(results)} character templates.")
    else:
        logging.debug("No character templates found for the given criteria.")

    return results

def get_char_temp(db: Session, char_id: int) -> Optional[CharTemp]:
    """
    透過 ID 高效率地檢索單一角色模板。

    Args:
        db (Session): 資料庫 session。
        char_id (int): 要檢索的角色模板 ID。

    Returns:
        Optional[CharTemp]: 找到的 CharTemp 物件，若不存在則回傳 None。
    """
    return db.get(CharTemp, char_id)


def delete_char_temp(db: Session, char_id: int) -> Optional[CharTemp]:
    """
    透過 ID 刪除一個角色模板。

    此函式僅將物件標記為刪除，並不會提交 transaction。

    Args:
        db (Session): 資料庫 session。
        char_id (int): 要刪除的角色模板 ID。

    Returns:
        Optional[CharTemp]: 被標記為刪除的 CharTemp 物件，若不存在則回傳 None。
    """
    char = db.get(CharTemp, char_id)
    if not char:
        return None
    db.delete(char)
    return char
