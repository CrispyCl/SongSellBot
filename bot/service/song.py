from logging import Logger
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, NoResultFound

from models import FileType, Genre, Song, SongTempo, SongType, User
from repository import GenreRepository, SongRepository


class SongService:
    """Song Service class"""

    def __init__(self, song_repo: SongRepository, genre_service: "GenreService", logger: Logger):
        self.song_repo = song_repo
        self.genre_serv = genre_service
        self.log = logger

    async def create(
        self,
        author_id: str,
        title: str,
        lyrics: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type_str: Optional[str] = None,
        type_str: str = "universal",
        tempo_str: str = "mid_tempo",
    ) -> int:
        try:
            file_type = FileType(file_type_str) if file_type_str else None
            type = SongType(type_str)
            tempo = SongTempo(tempo_str)
            return await self.song_repo.create(
                author_id=author_id,
                title=title,
                lyrics=lyrics,
                file_id=file_id,
                file_type=file_type,
                type=type,
                tempo=tempo,
            )
        except IntegrityError as e:
            self.log.warning("SongRepository: %s", e)
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return -1

    async def create_with_genres(
        self,
        author_id: str,
        title: str,
        genre_ids: List[str],
        lyrics: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type_str: Optional[str] = None,
        type_str: str = "universal",
        tempo_str: str = "mid_tempo",
    ) -> Optional[Song]:
        """Создает песню и присваивает ей список жанров"""
        try:
            song_id = await self.create(
                author_id,
                title,
                lyrics=lyrics,
                file_id=file_id,
                file_type_str=file_type_str,
                type_str=type_str,
                tempo_str=tempo_str,
            )
            if song_id < 0:
                return None
            for title in genre_ids:
                try:
                    genre = await self.genre_serv.get_or_create(title)
                    if not genre:
                        continue
                    await self.song_repo.add_genre(song_id, genre.id)
                except NoResultFound as ge:
                    self.log.warning("Genre или Song не найдены: %s", ge)
            song = await self.song_repo.get_one(song_id)
            return song
        except Exception as e:
            self.log.error("SongService.create_with_genres: %s", e)
            return None

    async def get_one(self, song_id: int) -> Optional[Song]:
        try:
            return await self.song_repo.get_one(song_id)
        except NoResultFound as e:
            self.log.warning("SongRepository: %s", e)
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return None

    async def get_by_title(self, title: str) -> Optional[Song]:
        try:
            return await self.song_repo.get_by_title(title)
        except NoResultFound as e:
            self.log.warning("SongRepository: %s", e)
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return None

    async def get_all(self) -> List[Song]:
        try:
            return await self.song_repo.get_all()
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return []

    async def get_customers(self, song_id: int) -> List[User]:
        try:
            return await self.song_repo.get_customers(song_id)
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return []

    async def get_by_filter(
        self,
        type_str: Optional[str],
        tempo_str: Optional[str],
        genre_titles: Optional[List[str]],
    ) -> List[Song]:
        try:
            type = None
            tempo = None
            genre_ids = []
            if type_str:
                type = SongType(type_str)
            if tempo_str:
                tempo = SongTempo(tempo_str)
            if genre_titles:
                for title in genre_titles:
                    genre = await self.genre_serv.get_or_create(title)
                    if not genre:
                        continue
                    genre_ids.append(genre.id)
            return await self.song_repo.get_by_filter(type, tempo, genre_ids)
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return []

    async def update(
        self,
        song_id: int,
        title: Optional[str] = None,
        lyrics: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type_str: Optional[str] = None,
        type_str: Optional[str] = None,
        tempo_str: Optional[str] = None,
    ) -> Optional[Song]:
        try:
            file_type = FileType(file_type_str) if file_type_str else None
            type = SongType(type_str) if type_str else None
            tempo = SongTempo(tempo_str) if tempo_str else None
            return await self.song_repo.update(
                id=song_id,
                title=title,
                lyrics=lyrics,
                file_id=file_id,
                file_type=file_type,
                type=type,
                tempo=tempo,
            )
        except NoResultFound as e:
            self.log.warning("SongRepository: %s", e)
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return None

    async def update_genres(self, song_id: int, genre_ids: List[int]) -> bool:
        try:
            song = await self.song_repo.get_one(song_id)
            if not song:
                return False

            # Очищаем текущие жанры
            for genre in song.genres:
                await self.song_repo.remove_genre(song_id=song_id, genre_id=genre.id)

            # Добавляем новые жанры
            for genre_id in genre_ids:
                await self.song_repo.add_genre(song_id=song_id, genre_id=genre_id)
            return True
        except Exception as e:
            self.log.error(f"SongRepository: error updating genres: {e}")
            return False

    async def delete(self, song_id: int) -> bool:
        try:
            await self.song_repo.delete(song_id)
            return True
        except NoResultFound as e:
            self.log.warning("SongRepository: %s", e)
        except Exception as e:
            self.log.error("SongRepository: %s", e)
        return False


class GenreService:
    """Genre Service class"""

    def __init__(self, repo: GenreRepository, logger: Logger):
        self.repo = repo
        self.log = logger

    async def create(self, title: str) -> int:
        try:
            return await self.repo.create(title)
        except IntegrityError as e:
            self.log.warning("GenreRepository: %s", e)
        except Exception as e:
            self.log.error("GenreRepository: %s", e)
        return -1

    async def get_one(self, genre_id: int) -> Optional[Genre]:
        try:
            return await self.repo.get_one(genre_id)
        except NoResultFound as e:
            self.log.warning("GenreRepository: %s", e)
        except Exception as e:
            self.log.error("GenreRepository: %s", e)
        return None

    async def get_by_title(self, title: str) -> Optional[Genre]:
        try:
            return await self.repo.get_by_title(title)
        except NoResultFound as e:
            self.log.warning("GenreRepository: %s", e)
        except Exception as e:
            self.log.error("GenreRepository: %s", e)
        return None

    async def get_all(self) -> List[Genre]:
        try:
            return await self.repo.get_all()
        except Exception as e:
            self.log.error("GenreRepository: %s", e)
        return []

    async def get_or_create(self, title: str) -> Optional[Genre]:
        try:
            genre = await self.get_by_title(title)
            if genre:
                return genre
            ganre_id = await self.create(title)
            return await self.get_one(ganre_id)
        except Exception as e:
            self.log.error("GenreRepository: %s", e)
        return None


__all__ = [
    "SongService",
    "GenreService",
]
