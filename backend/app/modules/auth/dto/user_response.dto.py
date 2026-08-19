import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    address: str | None = None
    phone_number: str | None = None
    birth_date: date | None = None

