from typing import Optional
from sqlalchemy.orm import Session, selectinload
from core_system.models.maps import Map
from core_system.models.association_tables import MapConnection, MapEventAssociation


def fetch_maps(
    db: Session,
    started_id: Optional[int],
    limit: int,
    direction: str = "next"
):
    query = db.query(Map)

    if started_id is not None:
        if direction == "next":
            query = query.filter(Map.id > started_id)
            query = query.order_by(Map.id.asc())
        else:
            query = query.filter(Map.id < started_id)
            query = query.order_by(Map.id.desc())
    else:
        query = query.order_by(Map.id.asc())

    maps = query.limit(limit).all()

    if direction == "prev":
        maps.reverse()

    return maps


def get_map_by_id(db: Session, map_id: int) -> Optional[Map]:
    """Retrieves a map by its ID, preloading related event and connection data."""
    return (
        db.query(Map)
        .options(
            selectinload(Map.event_associations).selectinload(MapEventAssociation.event),
            selectinload(Map.connections_a).selectinload(MapConnection.map_b),
            selectinload(Map.connections_b).selectinload(MapConnection.map_a),
        )
        .filter(Map.id == map_id)
        .first()
    )


def create_map_service(db: Session, name: str, description: Optional[str] = None, image_url: Optional[str] = None) -> Map:
    """Creates a new map and adds it to the session."""
    new_map = Map(
        name=name,
        description=description,
        image_url=image_url
    )
    db.add(new_map)
    db.flush()
    return new_map


def delete_map_service(db: Session, map_id: int) -> bool:
    """Deletes a map by its ID. Returns True if successful, False otherwise."""
    map_to_delete = db.query(Map).filter(Map.id == map_id).first()
    if not map_to_delete:
        return False
    db.delete(map_to_delete)
    db.commit()
    return True
