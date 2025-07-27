from sqlalchemy.orm import Session
from core_system.models.bo_admin import Admin
from util.auth import verify_password, create_access_token
from datetime import timedelta



class AuthenticationError(Exception):
    pass


def authenticate_user(db: Session, username: str, password: str) -> str:
    user = db.query(Admin).filter(Admin.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid username or password")

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=30)
    )
    return token


