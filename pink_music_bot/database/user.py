import datetime
from contextlib import AbstractAsyncContextManager
from typing import Callable

from gamdl.interface import SongCodec
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    delete,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True)
    songs_downloaded = Column(Integer, default=0, nullable=False)
    music_videos_downloaded = Column(Integer, default=0, nullable=False)
    fourk_download = Column(Boolean, default=False, nullable=False)
    synced_lyrics_file_upload = Column(Boolean, default=False, nullable=False)
    song_codec = Column(Enum(SongCodec), default=SongCodec.AAC_LEGACY, nullable=False)
    search_country = Column(String(2), default="US", nullable=False)
    last_free_credits_claim = Column(
        DateTime,
        default=None,
        nullable=True,
    )
    credits = Column(Integer, default=0, nullable=False)
    membership_due_date = Column(DateTime, default=None, nullable=True)

    def is_membership_active(self) -> bool:
        if self.membership_due_date is None:
            return False

        return self.membership_due_date > datetime.datetime.now()


class UserDatabase:
    def __init__(
        self,
        get_session: Callable[[], AbstractAsyncContextManager[AsyncSession]],
    ):
        self.get_session = get_session

    async def get(self, user_id: int) -> User | None:
        async with self.get_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def add_if_not_exists(self, user_id: int) -> User:
        async with self.get_session() as session:
            user = User(id=user_id)
            merged_user = await session.merge(user)
            return merged_user

    async def toggle_fourk_download(self, user_id: int) -> bool | None:
        async with self.get_session() as session:
            result = await session.execute(
                select(User.fourk_download).where(User.id == user_id)
            )
            current_value = result.scalar_one_or_none()
            if current_value is None:
                return None

            new_value = not current_value
            await session.execute(
                update(User).where(User.id == user_id).values(fourk_download=new_value)
            )
            return new_value

    async def toggle_synced_lyrics_file_upload(
        self,
        user_id: int,
    ) -> bool | None:
        async with self.get_session() as session:
            result = await session.execute(
                select(User.synced_lyrics_file_upload).where(User.id == user_id)
            )
            current_value = result.scalar_one_or_none()
            if current_value is None:
                return None

            new_value = not current_value
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(synced_lyrics_file_upload=new_value)
            )
            return new_value

    async def update_song_codec(self, user_id: int, codec: SongCodec) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(User).where(User.id == user_id).values(song_codec=codec)
            )

    async def update_search_country(self, user_id: int, country_code: str) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(search_country=country_code)
            )

    async def delete(self, user_id: int) -> bool:
        async with self.get_session() as session:
            result = await session.execute(delete(User).where(User.id == user_id))
            return result.rowcount > 0

    async def count(self) -> int:
        async with self.get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            return len(users)

    async def increment_songs_downloaded(self, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(songs_downloaded=User.songs_downloaded + 1)
            )

    async def increment_music_videos_downloaded(self, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(music_videos_downloaded=User.music_videos_downloaded + 1)
            )

    async def set_credits(self, user_id: int, credits: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(User).where(User.id == user_id).values(credits=credits)
            )

    async def update_last_free_credits_claim(
        self,
        user_id: int,
        claim_time: datetime.datetime,
    ) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_free_credits_claim=claim_time)
            )

    async def deduct_credits(self, user_id: int, credits: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(credits=User.credits - credits)
            )

    async def add_membership_days(self, user_id: int, days: int) -> datetime.datetime:
        async with self.get_session() as session:
            result = await session.execute(
                select(User.membership_due_date).where(User.id == user_id)
            )
            current_due_date = result.scalar_one_or_none()
            now = datetime.datetime.now()

            if current_due_date is None or current_due_date < now:
                new_due_date = now + datetime.timedelta(days=days)
            else:
                new_due_date = current_due_date + datetime.timedelta(days=days)

            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(membership_due_date=new_due_date)
            )

            return new_due_date

    async def count_members(self) -> int:
        async with self.get_session() as session:
            now = datetime.datetime.now()
            result = await session.execute(
                select(User).where(User.membership_due_date > now)
            )
            members = result.scalars().all()
            return len(members)
