from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Session

from core_system.models.event import Event
from core_system.models.maps import Map, MapArea
from core_system.models.association_tables import MapAreaEventAssociation


@dataclass
class EventAssociationDTO:
    event_id: int
    event_name: str
    probability: float


def update_map_area_event_associations(
    db: Session,
    map_id: int,
    area_id: int,
    upsert: Optional[List[dict]] = None,
    remove: Optional[List[int]] = None,
    normalize: bool = False,
) -> List[EventAssociationDTO]:
    map_obj = db.get(Map, map_id)
    if not map_obj:
        raise ValueError("Map not found")

    area_obj = (
        db.query(MapArea)
        .filter_by(id=area_id, map_id=map_id)
        .one_or_none()
    )
    if not area_obj:
        raise ValueError("MapArea not found or does not belong to map")

    if upsert:
        for ev in upsert:
            event_id = ev["event_id"]
            probability = ev["probability"]
            event_obj = db.get(Event, event_id)
            if not event_obj:
                raise ValueError(f"Event id {event_id} does not exist")

            existing = (
                db.query(MapAreaEventAssociation)
                .filter_by(map_area_id=area_id, event_id=event_id)
                .one_or_none()
            )
            if existing:
                existing.probability = probability
            else:
                new_assoc = MapAreaEventAssociation(
                    map_area_id=area_id,
                    event=event_obj,
                    probability=probability,
                )
                db.add(new_assoc)

    if remove:
        for eid in remove:
            assoc = (
                db.query(MapAreaEventAssociation)
                .filter_by(map_area_id=area_id, event_id=eid)
                .one_or_none()
            )
            if assoc:
                db.delete(assoc)

    if normalize:
        assocs = (
            db.query(MapAreaEventAssociation)
            .filter_by(map_area_id=area_id)
            .all()
        )
        total = sum(a.probability for a in assocs)
        if total > 0:
            for a in assocs:
                a.probability = a.probability / total

    db.flush()

    return [
        EventAssociationDTO(
            event_id=assoc.event.id,
            event_name=assoc.event.name,
            probability=assoc.probability,
        )
        for assoc in db.query(MapAreaEventAssociation).filter_by(map_area_id=area_id).all()
    ]


def patch_map_area_basic_service(
    db: Session,
    map_id: int,
    area_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
) -> MapArea:
    area_obj = (
        db.query(MapArea)
        .filter_by(id=area_id, map_id=map_id)
        .one_or_none()
    )
    if not area_obj:
        raise ValueError("MapArea not found or does not belong to map")

    if name is not None:
        area_obj.name = name
    if description is not None:
        area_obj.description = description
    if image_url is not None:
        area_obj.image_url = image_url

    db.flush()
    return area_obj


def delete_map_area_service(db: Session, map_id: int, area_id: int) -> bool:
    area_obj = (
        db.query(MapArea)
        .filter_by(id=area_id, map_id=map_id)
        .one_or_none()
    )
    if not area_obj:
        return False
    db.delete(area_obj)
    return True


def get_area_or_raise(db: Session, map_id: int, area_id: int) -> MapArea:
    area = (
        db.query(MapArea)
        .filter(
            MapArea.map_id == map_id,
            MapArea.id == area_id
        )
        .first()
    )
    if not area:
        raise LookupError("MapArea not found")
    return area


def create_map_area_service(
    db: Session,
    map_id: int,
    name: str,
    description: Optional[str],
    image_url: Optional[str],
) -> MapArea:
    parent_map = db.get(Map, map_id)
    if not parent_map:
        raise ValueError(f"Map with id {map_id} not found")

    new_area = MapArea(
        map_id=map_id,
        name=name,
        description=description,
        image_url=image_url,
    )
    db.add(new_area)
    db.flush()
    return new_area
