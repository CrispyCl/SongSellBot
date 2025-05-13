from typing import List

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import DefaultDatabase
from models import SongHistory, Wishlist


class WishlistRepository:
    """Wishlist Repository class"""

    def __init__(self, database: DefaultDatabase):
        self.db = database

    async def add(self, user_id: str, song_id: int) -> None:
        async with self.db.get_session() as session:
            session: AsyncSession
            entry = Wishlist(user_id=user_id, song_id=song_id)
            session.add(entry)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                # возможно уже в wishlist

    async def remove(self, user_id: str, song_id: int) -> None:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = delete(Wishlist).where(
                Wishlist.user_id == user_id,
                Wishlist.song_id == song_id,
            )
            await session.execute(stmt)
            await session.commit()


class SongHistoryRepository:
    """Song History Repository class"""

    def __init__(self, database: DefaultDatabase):
        self.db = database

    async def log(self, user_id: str, song_title: str, action: str = "view") -> int:
        async with self.db.get_session() as session:
            session: AsyncSession

            history = SongHistory(
                user_id=user_id,
                song_title=song_title,
                action=action,
            )
            session.add(history)
            await session.commit()
            return history.id

    async def get_by_user(self, user_id: str) -> List[SongHistory]:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = select(SongHistory).filter(SongHistory.user_id == user_id).order_by(SongHistory.viewed_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())


__all__ = ["WishlistRepository", "SongHistoryRepository"]
