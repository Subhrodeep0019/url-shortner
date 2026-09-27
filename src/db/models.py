from sqlmodel import SQLModel, Field

from datetime import datetime
from pydantic import EmailStr
from uuid import UUID, uuid4

class Link(SQLModel, table=True):
    __tablename__ = "links"

    uid: UUID = Field(default_factory=uuid4, primary_key=True)
    short_code: str = Field(index=True, unique=True)
    long_url: str
    custom_alias: str | None = Field(default=None,  unique=True, index=True)
    user_uid: UUID | None = Field(default=None, foreign_key="users.uid")
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: UUID = Field(default_factory=uuid4, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    hashed_pass: str
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)

class ClickLog(SQLModel, table=True):
    __tablename__ = "click_logs"

    uid: UUID = Field(default_factory=uuid4, primary_key=True)
    links_uid: UUID = Field(foreign_key="links.uid", index=True)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    referer: str | None = Field(default=None)
    user_agent: str

