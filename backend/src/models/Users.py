from datetime import datetime
from pydantic import ConfigDict
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, ForeignKey, Text
from sqlalchemy.orm import  relationship

from schemas.auth_schema import UserRole
from .Base import Base

class AppSession(Base):
    __tablename__="app_session"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(255), nullable=False)
    device = Column(String(255), nullable=False)
    refresh_token_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship(
        "Users",
        back_populates="sessions"
    )
    model_config = ConfigDict(from_attributes=True)

class Users(Base):
    __tablename__="users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.CANDIDATE
    )
    sessions = relationship(
        "AppSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    model_config = ConfigDict(from_attributes=True)