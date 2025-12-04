from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import Boolean, Column, Integer, String, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class MusicVideo(Base):
    __tablename__ = "music_video"

    id = Column(String(20), primary_key=True)
    fourk = Column(Boolean, primary_key=True)
    too_large = Column(Boolean, default=False, nullable=False)
    message_id = Column(Integer, nullable=True)


class MusicVideoDatabase:
    def __init__(
        self,
        get_session: Callable[[], AbstractAsyncContextManager[AsyncSession]],
    ):
        self.get_session = get_session

    async def add_if_not_exists(
        self,
        music_video_id: str,
        fourk: bool,
        message_id: int,
        too_large: bool = False,
    ) -> MusicVideo:
        async with self.get_session() as session:
            music_video = MusicVideo(
                id=music_video_id,
                fourk=fourk,
                message_id=message_id,
                too_large=too_large,
            )
            merged_music_video = await session.merge(music_video)
            return merged_music_video

    async def get(
        self,
        music_video_id: str,
        fourk: bool,
    ) -> MusicVideo | None:
        async with self.get_session() as session:
            result = await session.execute(
                select(MusicVideo).where(
                    MusicVideo.id == music_video_id, MusicVideo.fourk == fourk
                )
            )
            return result.scalar_one_or_none()

    async def delete(self, music_video_id: str, fourk: bool) -> bool:
        async with self.get_session() as session:
            result = await session.execute(
                delete(MusicVideo).where(
                    MusicVideo.id == music_video_id, MusicVideo.fourk == fourk
                )
            )
            return result.rowcount > 0

    async def count(self) -> int:
        async with self.get_session() as session:
            result = await session.execute(select(MusicVideo))
            music_videos = result.scalars().all()
            return len(music_videos)
