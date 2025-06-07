from sqlalchemy.orm import Session
from core_system.models.event import Event, GeneralEventLogic, EventResult, StoryTextData


# region event service
def create_event_service(db: Session, name: str, event_type: str, description: str = None):
    event = Event(name=name,
                  type=event_type,
                  description=description)
    db.add(event)
    db.commit()
    return event


def edit_event_service(db: Session, event_id: int, story_text: list[StoryTextData], description: str) -> Event:
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise ValueError(f"Event with id {event_id} not found.")

    if description is not None:
        event.description = description

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
# endregion


# region general logic
def edit_general_logic(db: Session, general_logic: GeneralEventLogic, story_text_list: list[StoryTextData] = None):
    if story_text_list:  # move to outside
        general_logic.set_story_text(story_text_list)
    db.commit()


def create_general_logic(db: Session, event_id: int):
    general_logic = GeneralEventLogic(event_id=event_id,
                                      story_text="[]",
                                      condition_json="[]")
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


def edit_event_result_service(db: Session, event_result_id: int, prior: int, story_text: list[StoryTextData], condition: list[dict]):
    event_result = db.query(EventResult).filter(
        EventResult.id == event_result_id).first()
    if story_text:
        event_result.set_story_text(story_text)
    if prior:
        event_result.prior = prior
    if condition:
        event_result.set_condition_list(condition)
    db.commit()
    return event_result
# endregion
