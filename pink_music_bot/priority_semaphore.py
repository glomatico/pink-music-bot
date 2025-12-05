import asyncio
from dataclasses import dataclass, field
from typing import Any
from contextlib import asynccontextmanager


@dataclass(order=True)
class PriorityItem:
    priority: int
    sequence: int  # Insertion order for FIFO within same priority
    event: asyncio.Event = field(compare=False)


class PrioritySemaphore:
    def __init__(self, value: int = 1):
        self._limit = value
        self._count = 0
        self._sequence = 0
        self._queue: asyncio.PriorityQueue[PriorityItem] = asyncio.PriorityQueue()
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self, priority: int = 0):
        async with self._lock:
            if self._count < self._limit:
                self._count += 1
                acquired_immediately = True
            else:
                acquired_immediately = False
                event = asyncio.Event()
                self._sequence += 1
                item = PriorityItem(
                    priority=priority, sequence=self._sequence, event=event
                )
                await self._queue.put(item)

        if not acquired_immediately:
            try:
                await event.wait()
            except asyncio.CancelledError:
                # If cancelled while waiting, check if we were already signaled
                if event.is_set():
                    # We got the semaphore, so we need to release it
                    await self._release()
                raise

        try:
            yield
        finally:
            await self._release()

    async def _release(self):
        async with self._lock:
            self._count -= 1
            if not self._queue.empty():
                self._count += 1
                item = self._queue.get_nowait()
                item.event.set()
