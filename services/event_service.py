import logging
from datetime import datetime
from typing import List, Optional, Union

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from core_system.models.association_tables import MapAreaEventAssociation, MapEventAssociation
from core_system.models.event import (Event, EventResult, GeneralEventLogic,
                                      StoryTextData, UserEventInstance)
from core_system.models.maps import Map, MapArea, UserMapProgress
from core_system.models.user import User, UserData
from schemas.event import (CharacterStateChange, DrawEventRequest,
                           DrawEventResponse)

# NOTE: The MonsterPoolEntry model might need adjustment for the logic in draw_current_map_event
from core_system.models.monsters import MonsterPoolEntry
from util.random_utils import weighted_choice
# from .condition_service import check_conditions # 您可以取消註解此行來使用條件檢查

# region event service
def fetch_events(
    db: Session,
    started_id: Optional[int],
    limit: int,
    direction: str = "next"
):
    query = db.query(Event)

    if started_id is not None:
        if direction == "next":
            query = query.filter(Event.id > started_id)
            query = query.order_by(Event.id.asc())
        else:
            query = query.filter(Event.id < started_id)
            query = query.order_by(Event.id.desc())
    else:
        query = query.order_by(Event.id.asc())

    events = query.limit(limit).all()

    if direction == "prev":
        events.reverse()

    return events


def create_event_service(db: Session, name: str, event_type: str, description: str = None):
    event = Event(name=name,
                  type=event_type,
                  description=description)
    db.add(event)
    return event


def edit_event_service(db: Session, event_id: int,
                       story_text: list[StoryTextData],
                       description: str,
                       name: str) -> Event:
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise ValueError(f"Event with id {event_id} not found.")

    if description is not None:
        event.description = description
    if name is not None:
        event.name = name
    if story_text is not None:
        if event.general_logic is None:
            raise ValueError(
                f"Event ID {event_id} has no associated general_logic.")
        event.general_logic.set_story_text(story_text)

    return event


def get_event_by_event_id(db: Session, event_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    return event


def delete_event(db: Session, event_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    db.delete(event)
    return
# endregion


# region general logic
def edit_general_logic(db: Session, general_logic: GeneralEventLogic, story_text_list: list[StoryTextData] = None):
    if story_text_list:  # move to outside
        general_logic.set_story_text(story_text_list)


def create_general_logic(db: Session, event_id: int):
    general_logic = GeneralEventLogic(event_id=event_id,
                                      story_text="[]")
    db.add(general_logic)
    db.flush(general_logic)
    return general_logic


def get_event_associations_for_map(db: Session, map_id: int) -> List[MapEventAssociation]:
    """
    根據 map_id 撈取所有地圖層級的事件關聯（包含機率）。

    Args:
        db (Session): 資料庫 session。
        map_id (int): 要查詢的地圖 ID。

    Raises:
        HTTPException: 如果找不到地圖。

    Returns:
        List[MapEventAssociation]: 包含事件與其機率的關聯物件列表。
    """
    stmt = (
        select(MapEventAssociation)
        .where(MapEventAssociation.map_id == map_id)
        .options(
            selectinload(MapEventAssociation.event)
        )
    )
    associations = db.scalars(stmt).all()
    if not associations:
        # 即使地圖存在但沒有事件，也會回傳空列表，所以這裡不用特別檢查地圖是否存在
        return []
    return associations


def get_event_associations_for_area(db: Session, area_id: int) -> List[MapAreaEventAssociation]:
    """
    根據 area_id 撈取所有區域層級的事件關聯（包含機率）。

    Args:
        db (Session): 資料庫 session。
        area_id (int): 要查詢的區域 ID。

    Raises:
        HTTPException: 如果找不到區域。

    Returns:
        List[MapAreaEventAssociation]: 包含事件與其機率的關聯物件列表。
    """
    stmt = (
        select(MapAreaEventAssociation)
        .where(MapAreaEventAssociation.map_area_id == area_id)
        .options(
            selectinload(MapAreaEventAssociation.event)
        )
    )
    associations = db.scalars(stmt).all()
    return associations
# endregion


# region event result
def get_event_result(db: Session, event_result_id: int):
    event_result = db.query(EventResult).filter(
        EventResult.id == event_result_id).first()
    return event_result


def create_event_result_service(db: Session, name: str, general_event_logic_id: int, reward_pool_id: int = None):
    event_result = EventResult(name=name,
                               reward_pool_id=reward_pool_id,
                               general_event_logic_id=general_event_logic_id
                               )
    db.add(event_result)
    db.flush(event_result)
    return event_result


def edit_event_result_service(db: Session,name:str, event_result_id: int, prior: int, story_text: list[StoryTextData], condition: list[dict], status_effects_json: list[dict]):
    logging.info(f"Check go to edit_event_result_service")
    event_result = db.query(EventResult).filter(
        EventResult.id == event_result_id).first()
    if name:
        event_result.name = name
    if story_text:
        logging.info(f"Check: {story_text}")
        event_result.set_story_text(story_text)
    if prior is not None:
        event_result.prior = prior
    if condition:
        event_result.set_condition_list(condition)
    if status_effects_json:
        event_result.set_status_effects_json(status_effects_json)
    return event_result


def delete_event_result(db: Session, result_id: int):
    event_result = db.query(EventResult).filter(
        EventResult.id == result_id).first()
    db.delete(event_result)
    db.commit()
    return
# endregion


# region draw event
def draw_current_map_event(
    db: Session,
    user: User,
    payload: DrawEventRequest,
) -> DrawEventResponse:
    # 1. 取出 user_data + current map/area 並驗證
    user_data = db.scalar(
        select(UserData)
        .where(UserData.user_id == user.id)
        .options(selectinload(UserData.current_map), selectinload(UserData.current_area))
    )
    if not user_data:
        raise HTTPException(status_code=404, detail="User data missing")
    if not user_data.current_map or not user_data.current_area:
        raise HTTPException(status_code=400, detail="Current map/area not set")
    if payload.map_id != user_data.current_map.id or payload.area_id != user_data.current_area.id:
        raise HTTPException(
            status_code=400,
            detail="Client provided map/area doesn't match server record"
        )

    # 2. 鎖定 progress row
    progress = db.scalar(
        select(UserMapProgress)
        .where(
            and_(
                UserMapProgress.user_data_id == user_data.id,
                UserMapProgress.map_id == user_data.current_map.id,
            )
        )
        .with_for_update()
    )
    if not progress:
        progress = UserMapProgress(
            user_data_id=user_data.id,
            map_id=user_data.current_map.id,
            exploration_score=0,
        )
        db.add(progress)
        db.flush()

    # 3. 撈 map + area event pool（只 active 的）
    # 現在回傳的是包含機率的 Association 物件
    map_associations = get_event_associations_for_map(db, user_data.current_map.id)
    area_associations = get_event_associations_for_area(db, user_data.current_area.id)

    all_associations = map_associations + area_associations

    # 準備加權選擇的候選列表，格式為 (物件, 權重)
    candidate_templates = [
        (assoc.event, assoc.probability) for assoc in all_associations
    ]
    
    if not candidate_templates:
        raise HTTPException(status_code=400, detail="No available events to draw")

    # NOTE: 在這裡您可以使用 check_conditions 過濾 candidate_templates
    # 之後再傳遞給 weighted_choice
    chosen_template: Event = weighted_choice(candidate_templates)
    if not chosen_template:
        raise HTTPException(status_code=500, detail="Failed to pick an event")

    if chosen_template.type == "battle":
        result_text = "你遭遇了怪物，準備戰鬥！"
    else:
        pass

    # 9. 建 response
    resp = DrawEventResponse(
        event_type=chosen_template.type,
        event_template_id=chosen_template.id,
        story_text=story_text,
        result_text=result_text,
        character_changes=character_changes,
        extra=event_payload,
    )
    return resp
# endregion