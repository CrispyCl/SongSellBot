from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database import DefaultDatabase
from models import Genre, GenreToSong, Song, SongTempo, SongType


class SongRepository:
    """Song Repository class"""

    def __init__(self, database: DefaultDatabase):
        self.db = database

    async def create(
        self,
        author_id: str,
        title: str,
        lyrics: Optional[str] = None,
        file_id: Optional[str] = None,
        type: SongType = SongType.universal,
        tempo: SongTempo = SongTempo.mid_tempo,
    ) -> int:
        async with self.db.get_session() as session:
            session: AsyncSession
            song = Song(
                author_id=author_id,
                title=title,
                lyrics=lyrics,
                file_id=file_id,
                type=type,
                tempo=tempo,
            )
            session.add(song)
            try:
                await session.commit()
                return song.id
            except Exception as e:
                await session.rollback()
                raise e

    async def add_genre(self, song_id: int, genre_id: int) -> None:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = GenreToSong(song_id=song_id, genre_id=genre_id)

            session.add(stmt)
            await session.commit()

    async def get_one(self, id: int) -> Optional[Song]:
        async with self.db.get_session() as session:
            session: AsyncSession
            song = await session.get(Song, id)
            if not song:
                raise NoResultFound(f"Song with id={id} does not exist")
            return song

    async def get_all(self) -> List[Song]:
        async with self.db.get_session() as session:
            session: AsyncSession
            result = await session.execute(select(Song).order_by(Song.id))
            return list(result.scalars().all())

    async def update(
        self,
        id: int,
        title: Optional[str] = None,
        lyrics: Optional[str] = None,
        file_id: Optional[str] = None,
        type: Optional[SongType] = None,
        tempo: Optional[SongTempo] = None,
    ) -> Song:
        async with self.db.get_session() as session:
            session: AsyncSession
            song = await session.get(Song, id)
            if not song:
                raise NoResultFound(f"Song with id={id} does not exist")
            if title is not None:
                song.title = title
            if lyrics is not None:
                song.lyrics = lyrics
            if file_id is not None:
                song.file_id = file_id
            if type is not None:
                song.type = type
            if tempo is not None:
                song.tempo = tempo
            await session.commit()
            await session.refresh(song)
            return song

    async def delete(self, id: int) -> None:
        async with self.db.get_session() as session:
            session: AsyncSession
            song = await session.get(Song, id)
            if not song:
                raise NoResultFound(f"Song with id={id} does not exist")
            await session.delete(song)
            await session.commit()


class GenreRepository:
    """Genre Repository class"""

    def __init__(self, database: DefaultDatabase):
        self.db = database

    async def create(self, title: str) -> int:
        async with self.db.get_session() as session:
            session: AsyncSession
            genre = Genre(title=title)
            session.add(genre)
            try:
                await session.commit()
                return genre.id
            except IntegrityError:
                await session.rollback()
                raise

    async def get_one(self, id: int) -> Genre:
        async with self.db.get_session() as session:
            session: AsyncSession
            genre = await session.get(Genre, id)
            if not genre:
                raise NoResultFound(f"Genre with id={id} does not exist")
            return genre

    async def get_by_title(self, title: str) -> Genre:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = select(Genre).filter(Genre.title == title)
            genre = (await session.execute(stmt)).scalar_one_or_none()
            if not genre:
                raise NoResultFound(f"Genre with title='{title}' does not exist")
            return genre

    async def get_all(self) -> List[Genre]:
        async with self.db.get_session() as session:
            session: AsyncSession
            result = await session.execute(select(Genre).order_by(Genre.id))
            return list(result.scalars().all())


__all__ = [
    "SongRepository",
    "GenreRepository",
]
