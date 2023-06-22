import unittest
from asyncio import Future, Task
from typing import Coroutine
from unittest.mock import AsyncMock, patch, MagicMock

from brain_conductor.utils import TaskManager


class TaskManagerTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """setup"""
        patcher = patch("brain_conductor.utils.asyncio")
        self._asyncio = patcher.start()
        self.addCleanup(patcher.stop)
        self._task = MagicMock(Task)
        self._asyncio.create_task.return_value = self._task
        self._app_task_manager = TaskManager()

    async def test_create_task_calls_asyncio_create_task(self):
        coro = AsyncMock(Future)
        with self._app_task_manager as atm:
            atm.create_task("Hello", coro)
            self._asyncio.create_task.assert_called_once_with(coro, name="Hello")

    async def test_raises_runtime_error_when_not_in_context_manager(self):
        coro = AsyncMock()
        with self.assertRaisesRegex(RuntimeError, "Must be run via context manager"):
            self._app_task_manager.create_task("name", coro)

    async def test_assert_cancels_incomplete_tasks_only_on_context_exit(self):
        coro = AsyncMock()
        with self._app_task_manager as atm:
            atm.create_task("task", coro)
            self._task.cancel.assert_not_called()
        self._task.cancel.assert_called_once()

    async def test_create_task_returns_task_instance(self):
        coro = AsyncMock(Coroutine)
        with self._app_task_manager as atm:
            task = atm.create_task("task", coro)
            self.assertIsInstance(task, Task)


if __name__ == "__main__":
    unittest.main()
