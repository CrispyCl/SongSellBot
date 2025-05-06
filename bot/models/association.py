from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Wishlist(Base):
    __tablename__ = "wishlist"

    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True)


class SongHistory(Base):
    __tablename__ = "view_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id", ondelete="CASCADE"))
    song_title: Mapped[str] = mapped_column(String(150), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    action: Mapped[str] = mapped_column(String(20), default="view")

    user = relationship("User", back_populates="view_history")

    def __repr__(self):
        return f"<SongHistory(user={self.user_id}, song_title={self.song_title}, action={self.action})>"


__all__ = ["Wishlist"]
