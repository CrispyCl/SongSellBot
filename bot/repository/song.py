from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import DefaultDatabase
from models import FileType, Genre, GenreToSong, Song, SongTempo, SongType, User


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
        file_type: Optional[FileType] = None,
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
                file_type=file_type,
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
            try:
                session: AsyncSession
                exists = await session.scalar(
                    select(GenreToSong)
                    .where(GenreToSong.song_id == song_id, GenreToSong.genre_id == genre_id)
                    .limit(1),
                )

                if exists:
                    return

                stmt = GenreToSong(song_id=song_id, genre_id=genre_id)
                session.add(stmt)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise e

    async def remove_genre(self, song_id: int, genre_id: int) -> None:
        async with self.db.get_session() as session:
            try:
                session: AsyncSession
                result = await session.execute(
                    delete(GenreToSong).where(GenreToSong.song_id == song_id, GenreToSong.genre_id == genre_id),
                )

                if result.rowcount == 0:
                    return  # Связь не найдена
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    async def get_one(self, id: int) -> Optional[Song]:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = select(Song).where(Song.id == id).options(joinedload(Song.genres))

            result = await session.execute(stmt)
            song = result.scalars().first()
            if not song:
                raise NoResultFound(f"Song with id={id} does not exist")
            return song

    async def get_by_title(self, title: str) -> Song:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = select(Song).where(Song.title == title).options(joinedload(Song.genres))

            result = await session.execute(stmt)
            song = result.scalars().first()
            if not song:
                raise NoResultFound(f"Song with title={title} does not exist")
            return song

    async def get_all(self) -> List[Song]:
        async with self.db.get_session() as session:
            session: AsyncSession
            result = await session.execute(select(Song).order_by(Song.id))
            return list(result.scalars().all())

    async def get_by_filter(
        self,
        type: Optional[SongType],
        tempo: Optional[SongTempo],
        genre_ids: List[int],
    ) -> List[Song]:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = select(Song)
            if type is not None:
                stmt = stmt.where(Song.type == type)
            if tempo is not None:
                stmt = stmt.where(Song.tempo == tempo)
            if genre_ids:
                stmt = stmt.join(GenreToSong).where(GenreToSong.genre_id.in_(genre_ids))
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_customers(self, id: int) -> List[User]:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = select(Song).options(selectinload(Song.customers)).filter(Song.id == id)
            result = await session.execute(stmt)
            song: Optional[Song] = result.scalars().first()

            if not song:
                raise NoResultFound(f"Song with id={id} does not exist")
            return song.customers

    async def update(
        self,
        id: int,
        title: Optional[str] = None,
        lyrics: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[FileType] = None,
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
            if file_type is not None:
                song.file_type = file_type
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

    async def get_by_type_and_tempo(self, song_type: SongType, tempo: SongTempo) -> List[Genre]:
        async with self.db.get_session() as session:
            session: AsyncSession
            stmt = (
                select(Genre)
                .join(GenreToSong, Genre.id == GenreToSong.genre_id)
                .join(Song, GenreToSong.song_id == Song.id)
                .where(Song.type == song_type, Song.tempo == tempo)
                .distinct()
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())


__all__ = [
    "SongRepository",
    "GenreRepository",
]
