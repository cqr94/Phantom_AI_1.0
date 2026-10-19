from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import (
    ForeignKey,
    String,
    Boolean,
)

from agent.db import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str]

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id")
    )

    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    mfa_secret: Mapped[str | None]

    role = relationship("Role")