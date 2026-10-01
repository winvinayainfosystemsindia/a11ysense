"""
In-process async task queue replacing Redis Streams.
Runs background tasks (crawler, auditor) safely in isolated Proactor event loops on Windows.
"""
import sys
import asyncio
import logging
import threading
import traceback
from typing import Callable, Coroutine, Any

logger = logging.getLogger("a11ysense.task_queue")

class TaskQueue:
    def __init__(self):
        self._tasks = set()

    def run_task(self, coro_fn: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs):
        """
        Schedule a background task in an isolated Proactor event loop thread on Windows
        or in the running event loop on Linux/macOS.
        """
        if sys.platform == "win32":
            def _worker():
                try:
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    loop = asyncio.ProactorEventLoop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(coro_fn(*args, **kwargs))
                    finally:
                        loop.close()
                except Exception as e:
                    logger.error(f"Background task failed in Proactor thread: {e}\n{traceback.format_exc()}")

            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            return t
        else:
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
