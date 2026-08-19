import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)  # type: ignore[arg-type]
        return self.db.execute(stmt).scalar_one_or_none()

    def exists_by_email(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

