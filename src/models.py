import uuid

import timestamp
from sqlalchemy import Enum, ForeignKey, Integer, String, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoleEnum(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"


class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[timestamp]

    users: Mapped[list] = relationship(
        "User", back_populates="group", order_by="User.username", lazy="joined"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid] = mapped_column(
        types.Uuid(), primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str]
    surname: Mapped[str]
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    role: Mapped[RoleEnum] = mapped_column(RoleEnum, default=RoleEnum.USER)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    image_s3_path: Mapped[str] = mapped_column(String(1024))
    is_blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[timestamp]
    modified_at: Mapped[timestamp]

    group: Mapped[list] = relationship(
        "Group", back_populates="users", order_by="Group.id", lazy="joined"
    )
