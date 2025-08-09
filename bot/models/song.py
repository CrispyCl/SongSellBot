from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class FileType(PyEnum):
    video = "video"
    audio = "audio"


class SongType(PyEnum):
    universal = "universal"
    male = "male"
    female = "female"
    duet = "duet"


class SongTempo(PyEnum):
    dance = "dance"
    mid_tempo = "mid_tempo"
    slow = "slow"


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    lyrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_type: Mapped[Optional[FileType]] = mapped_column(SqlEnum(FileType), default=FileType.video, nullable=True)
    type: Mapped[SongType] = mapped_column(SqlEnum(SongType), default=SongType.universal)
    tempo: Mapped[SongTempo] = mapped_column(SqlEnum(SongTempo), default=SongTempo.mid_tempo)

    author = relationship("User")
    genres: Mapped[List["Genre"]] = relationship("Genre", secondary="genre_to_song", back_populates="songs")
    customers = relationship("User", secondary="wishlist", back_populates="wishlist")

    def __repr__(self):
        return f"<Song(id={self.id}, title={self.title})>"


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)

    songs: Mapped[List["Song"]] = relationship("Song", secondary="genre_to_song", back_populates="genres")

    def __repr__(self):
        return f"<Genre(id={self.id}, title={self.title})>"


class GenreToSong(Base):
    __tablename__ = "genre_to_song"

    genre_id: Mapped[int] = mapped_column(Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)
    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True)


__all__ = ["FileType", "Song", "SongType", "SongTempo", "Genre", "GenreToSong"]
