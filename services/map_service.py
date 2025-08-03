from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

from sqlalchemy.orm import Session, selectinload

from core_system.models.event import Event
from core_system.models.maps import Map
from core_system.models.association_tables import MapConnection, MapEventAssociation
from schemas.map import CreateMapData


# ---------------------- DTOs / Helpers ----------------------


@dataclass
class EventAssociationDTO:
    event_id: int
    event_name: str
    probability: float


@dataclass
class CreatedMapInfoDTO:
    id: int
    name: str


# ---------------------- Map Basic ----------------------


def patch_map_basic_service(
    db: Session,
    map_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
) -> Map:
    """
    更新 Map 的基本屬性（name / description / image_url），
    若找不到地圖會拋 ValueError。
    """
    map_obj = db.get(Map, map_id)
    if not map_obj:
        raise ValueError("Map not found")

    if name is not None:
        map_obj.name = name
    if description is not None:
        map_obj.description = description
    if image_url is not None:
        map_obj.image_url = image_url

    return map_obj


# ---------------------- Event Associations ----------------------


def update_map_event_associations(
    db: Session,
    map_id: int,
    upsert: Optional[List[dict]] = None,  # each dict must have 'event_id' and 'probability'
    remove: Optional[List[int]] = None,
    normalize: bool = False,
) -> List[EventAssociationDTO]:
    """
    Upsert / remove event associations for a map. 可選擇正規化機率總和。
    """
    map_obj = db.get(Map, map_id)
    if not map_obj:
        raise ValueError("Map not found")

    # Upsert
    if upsert:
        for ev in upsert:
            event_id = ev["event_id"]
            probability = ev["probability"]
            event_obj = db.get(Event, event_id)
            if not event_obj:
                raise ValueError(f"Event id {event_id} does not exist")

            existing = (
                db.query(MapEventAssociation)
                .filter_by(map_id=map_obj.id, event_id=event_id)
                .one_or_none()
            )
            if existing:
                existing.probability = probability
            else:
                new_assoc = MapEventAssociation(
                    map=map_obj,
                    event=event_obj,
                    probability=probability,
                )
                db.add(new_assoc)

    # Remove
    if remove:
        for eid in remove:
            assoc = (
                db.query(MapEventAssociation)
                .filter_by(map_id=map_obj.id, event_id=eid)
                .one_or_none()
            )
            if assoc:
                db.delete(assoc)

    # Normalize total probability to 1 if requested
    if normalize:
        assocs = (
            db.query(MapEventAssociation)
            .filter_by(map_id=map_obj.id)
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
        for assoc in map_obj.event_associations
    ]


# ---------------------- Cursor-based Fetch ----------------------


def fetch_maps(
    db: Session,
    cursor_id: Optional[int],
    limit: int,
    direction: Literal["next", "prev"] = "next",
) -> Tuple[List[Map], Optional[int], Optional[int], bool]:
    """
    Cursor-based 分頁邏輯。
    回傳：maps（最多 limit 筆）、next_cursor、prev_cursor、has_more（是否還有更多）。
    direction="next" 表示從 cursor_id 之後往前抓（升冪）；
    direction="prev" 表示從 cursor_id 之前往回抓（降冪但最後會反向回傳正序）。
    """
    query = db.query(Map)

    if direction == "next":
        if cursor_id is not None:
            query = query.filter(Map.id > cursor_id)
        query = query.order_by(Map.id.asc())
    else:  # prev
        if cursor_id is not None:
            query = query.filter(Map.id < cursor_id)
        query = query.order_by(Map.id.desc())

    results = query.limit(limit + 1).all()
    has_more = len(results) > limit
    if has_more:
        results = results[:limit]

    if direction == "prev":
        results = list(reversed(results))

    next_cursor = results[-1].id if results else None
    prev_cursor = results[0].id if results else None

    return results, next_cursor, prev_cursor, has_more


# ---------------------- Get Single Map with Eager Loading ----------------------


def get_map_by_id(db: Session, map_id: int) -> Optional[Map]:
    """
    Retrieves a map by its ID, preloading related event associations and connections.
    """
    return (
        db.query(Map)
        .options(
            selectinload(Map.event_associations).selectinload(
                MapEventAssociation.event
            ),
            selectinload(Map.connections_a).selectinload(MapConnection.map_b),
            selectinload(Map.connections_b).selectinload(MapConnection.map_a),
        )
        .filter(Map.id == map_id)
        .first()
    )


# ---------------------- Map Creation / Deletion ----------------------


def create_maps_service(
    db: Session,
    map_datas: List[CreateMapData],
) -> List[CreatedMapInfoDTO]:
    """
    批量建立地圖，回傳已建立的簡要資訊。
    """
    created: List[CreatedMapInfoDTO] = []
    for md in map_datas:
        new_map = Map(
            name=md.name,
            description=md.description,
            image_url=getattr(md, "image_url", None),
        )
        db.add(new_map)
        db.flush()  # 取得 new_map.id
        created.append(CreatedMapInfoDTO(id=new_map.id, name=new_map.name))
    return created


def delete_map_service(db: Session, map_id: int) -> bool:
    """
    刪除指定 map，成功回傳 True；找不到回傳 False。
    """
    map_to_delete = db.query(Map).filter(Map.id == map_id).first()
    if not map_to_delete:
        return False
    db.delete(map_to_delete)
    return True


# ---------------------- Connections ----------------------


def get_ordered_pair(id1: int, id2: int) -> Tuple[int, int]:
    return (id1, id2) if id1 < id2 else (id2, id1)


def upsert_connection(
    session: Session,
    map_obj: Map,
    neighbor: Map,
    **kwargs,
) -> MapConnection:
    """
    依照 map id 排序保證無方向唯一性，upsert 連線。
    """
    a, b = (map_obj, neighbor) if map_obj.id < neighbor.id else (neighbor, map_obj)
    conn = (
        session.query(MapConnection)
        .filter_by(map_a_id=a.id, map_b_id=b.id)
        .one_or_none()
    )
    if conn is None:
        conn = MapConnection(map_a=a, map_b=b, **kwargs)
        session.add(conn)
    else:
        for key, val in kwargs.items():
            setattr(conn, key, val)
    return conn


def remove_connection(session: Session, map_obj: Map, neighbor: Map):
    a_id, b_id = get_ordered_pair(map_obj.id, neighbor.id)
    conn = (
        session.query(MapConnection)
        .filter_by(map_a_id=a_id, map_b_id=b_id)
        .one_or_none()
    )
    if conn:
        session.delete(conn)


def patch_map_connections_service(
    db: Session,
    map_id: int,
    connections: Optional[List[dict]] = None,
    remove_connections: Optional[List[int]] = None,
) -> Map:
    """
    Upsert / remove 與該 map 的鄰居連線，回傳更新後的 Map（包含 connections_a/b）。
    """
    map_obj = db.get(Map, map_id)
    if not map_obj:
        raise ValueError("Map not found")

    # upsert connections
    if connections:
        for conn_in in connections:
            neighbor_id = conn_in["neighbor_id"]
            if neighbor_id == map_obj.id:
                continue
            neighbor = db.get(Map, neighbor_id)
            if not neighbor:
                raise ValueError(f"Neighbor map id {neighbor_id} does not exist")
            upsert_connection(
                db,
                map_obj,
                neighbor,
                is_locked=conn_in.get("is_locked", False),
                required_item=conn_in.get("required_item"),
                required_level=conn_in.get("required_level", 0),
            )

    # remove connections
    if remove_connections:
        for nid in remove_connections:
            if nid == map_obj.id:
                continue
            neighbor = db.get(Map, nid)
            if neighbor:
                remove_connection(db, map_obj, neighbor)

    return map_obj
