from contextlib import AbstractAsyncContextManager
from typing import Callable

from gamdl.interface import SongCodec
from sqlalchemy import Column, Enum, Integer, String, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class Song(Base):
    __tablename__ = "song"

    id = Column(String(20), primary_key=True)
    codec = Column(Enum(SongCodec), nullable=False, primary_key=True)
    message_id_song = Column(Integer, nullable=False)
    message_id_synced_lyrics = Column(Integer, nullable=True, default=None)


class SongDatabase:
    def __init__(
        self,
        get_session: Callable[[], AbstractAsyncContextManager[AsyncSession]],
    ):
        self.get_session = get_session

    async def get(self, song_id: str, codec: SongCodec) -> Song | None:
        async with self.get_session() as session:
            result = await session.execute(
                select(Song).where(
                    Song.id == song_id,
                    Song.codec == codec,
                )
            )
            return result.scalar_one_or_none()

    async def add_if_not_exists(
        self,
        song_id: str,
        codec: SongCodec,
        message_id_song: int,
        message_id_synced_lyrics: int | None = None,
    ) -> Song:
        async with self.get_session() as session:
            song = Song(
                id=song_id,
                codec=codec,
                message_id_song=message_id_song,
                message_id_synced_lyrics=message_id_synced_lyrics,
            )
            merged_song = await session.merge(song)
            return merged_song

    async def delete(self, song_id: str, codec: SongCodec) -> bool:
        async with self.get_session() as session:
            result = await session.execute(
                delete(Song).where(Song.id == song_id, Song.codec == codec)
            )
            return result.rowcount > 0

    async def count(self) -> int:
        async with self.get_session() as session:
            result = await session.execute(select(func.count()).select_from(Song))
            return result.scalar_one()
