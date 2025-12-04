from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .base import Base
from .music_video import MusicVideoDatabase
from .song import SongDatabase
from .user import UserDatabase


class Database:
    def __init__(
        self,
        database_url: str,
    ) -> None:
        self.database_url = database_url

    @classmethod
    async def create(cls, database_url: str) -> None:
        database = cls(database_url)
        await database.initialize()
        return database

    async def initialize(self) -> None:
        self.music_video = MusicVideoDatabase(self.get_session)
        self.song = SongDatabase(self.get_session)
        self.user = UserDatabase(self.get_session)

        self.engine = create_async_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            future=True,
        )

        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        session = self.session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
