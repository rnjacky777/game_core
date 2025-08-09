from typing import List, Optional
from sqlalchemy.orm import Session
from core_system.models import CharTemp
from schemas.char_temp import CharTempCreate, CharTempUpdate


def create_char_temp(db: Session, char_data: CharTempCreate) -> CharTemp:
    """
    建立一個新的角色模板實例並將其加入到 session 中。
    此函式不會提交 transaction。
    """
    char = CharTemp(**char_data.model_dump())
    db.add(char)
    db.flush()
    db.refresh(char)
    return char


def get_all_char_temps(db: Session, skip: int = 0, limit: int = 100) -> List[CharTemp]:
    """
    使用分頁檢索角色模板列表。
    """
    return db.query(CharTemp).offset(skip).limit(limit).all()


def get_char_temp(db: Session, char_id: int) -> Optional[CharTemp]:
    """
    透過 ID 檢索單一角色模板。
    為了效率，使用 db.get()。
    """
    return db.get(CharTemp, char_id)


def update_char_temp(db: Session, char_id: int, char_data: CharTempUpdate) -> Optional[CharTemp]:
    """
    使用新資料更新現有的角色模板。
    只更新輸入資料中明確設定的欄位。
    """
    char = db.get(CharTemp, char_id)
    if not char:
        return None

    update_data = char_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(char, key, value)

    db.add(char)
    return char


def delete_char_temp(db: Session, char_id: int) -> Optional[CharTemp]:
    """
    透過 ID 刪除一個角色模板。
    將物件標記為刪除，但不提交 transaction。
    """
    char = db.get(CharTemp, char_id)
    if not char:
        return None
    db.delete(char)
    return char
