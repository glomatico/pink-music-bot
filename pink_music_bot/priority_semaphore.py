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

    @asynccontextmanager
    async def acquire(self, priority: int = 0):
        if self._count < self._limit:
            self._count += 1
            try:
                yield
            finally:
                self._release()
            return

        event = asyncio.Event()
        self._sequence += 1
        item = PriorityItem(priority=priority, sequence=self._sequence, event=event)
        await self._queue.put(item)
        await event.wait()

        try:
            yield
        finally:
            self._release()

    def _release(self):
        self._count -= 1
        if not self._queue.empty():
            self._count += 1
            item = self._queue.get_nowait()
            item.event.set()
