from sqlalchemy.orm import Session
from core_system.models import CharTemp
from schemas.char_temp import CharTempCreate

def create_char_temp(db: Session, char_data: CharTempCreate) -> CharTemp:
    char = CharTemp(**char_data.model_dump())
    db.add(char)
    # db.commit() 拿掉，改由呼叫端負責
    db.flush()  # 可選，讓 char.id 等生成（還沒 commit，但先同步到 session）
    db.refresh(char)
    return char