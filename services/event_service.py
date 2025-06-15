import logging
from typing import Optional
from sqlalchemy.orm import Session
from core_system.models.event import Event, GeneralEventLogic, EventResult, StoryTextData


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
    db.commit()
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

    db.commit()
    db.refresh(event)
    return event


def get_event_by_event_id(db: Session, event_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    return event


def delete_event(db: Session, event_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    db.delete(event)
    db.commit()
    return
# endregion


# region general logic
def edit_general_logic(db: Session, general_logic: GeneralEventLogic, story_text_list: list[StoryTextData] = None):
    if story_text_list:  # move to outside
        general_logic.set_story_text(story_text_list)
    db.commit()


def create_general_logic(db: Session, event_id: int):
    general_logic = GeneralEventLogic(event_id=event_id,
                                      story_text="[]")
    db.add(general_logic)
    db.commit()
    db.flush(general_logic)
    return general_logic
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
    db.commit()
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
    if prior:
        event_result.prior = prior
    if condition:
        event_result.set_condition_list(condition)
    if status_effects_json:
        event_result.set_status_effects_json(status_effects_json)
    db.commit()
    return event_result


def delete_event_result(db: Session, result_id: int):
    event_result = db.query(EventResult).filter(
        EventResult.id == result_id).first()
    db.delete(event_result)
    db.commit()
    return
# endregion
