import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoleEnum(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"


class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users = relationship(
        "User", back_populates="group", order_by="User.username", lazy="joined"
    )


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid] = mapped_column(
        types.Uuid(), primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=True)
    surname: Mapped[str] = mapped_column(Text, nullable=True)
    username: Mapped[str] = mapped_column(Text, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(Text)
    phone_number: Mapped[str] = mapped_column(Text, unique=True, nullable=True)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.USER)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("group.id"), nullable=True
    )
    image_s3_path: Mapped[str] = mapped_column(Text, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    group = relationship(
        "Group", back_populates="users", order_by="Group.id", lazy="joined"
    )

    def to_dict(self):
        user_dict = self.__dict__
        user_dict["id"] = str(user_dict["id"])
        return user_dict
