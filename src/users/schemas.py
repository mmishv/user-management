from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserPatchData(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    group_id: Optional[int] = None


class UserData(UserPatchData):
    id: str
    is_blocked: bool
    created_at: datetime
    modified_at: Optional[datetime]
    role: str
    image_s3_path: Optional[str] = None
    image: Optional[bytes] = None
