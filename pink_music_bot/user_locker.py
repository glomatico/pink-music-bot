import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator


class UserLocker:
    def __init__(
        self,
    ):
        self.users: set[int] = set()
        self.users_lock = asyncio.Lock()

    def is_user_locked(self, user_id: int) -> bool:
        return user_id in self.users

    @asynccontextmanager
    async def acquire_user_lock(self, user_id: int) -> AsyncIterator[None]:
        async with self.users_lock:
            self.users.add(user_id)

        try:
            yield
        finally:
            async with self.users_lock:
                self.users.discard(user_id)
