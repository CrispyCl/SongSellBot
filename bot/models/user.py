from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(20), primary_key=True)
    username = Column(String(32), nullable=False)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    date_joined = Column(DateTime, default=datetime.now())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, is_staff={self.is_staff})>"


__all__ = ["User"]
