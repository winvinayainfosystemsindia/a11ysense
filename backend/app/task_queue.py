"""
In-process async task queue replacing Redis Streams.
Runs background tasks (crawler, auditor) safely in python asyncio event loop.
"""
import asyncio
import logging
import traceback
from typing import Callable, Coroutine, Any

logger = logging.getLogger("a11ysense.task_queue")

class TaskQueue:
    def __init__(self):
        self._tasks = set()

    def run_task(self, coro_fn: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> asyncio.Task:
        """Schedule a background task in the running event loop."""
        async def _wrapper():
            try:
                await coro_fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"Background task failed: {e}\n{traceback.format_exc()}")

        task = asyncio.create_task(_wrapper())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

task_queue = TaskQueue()
