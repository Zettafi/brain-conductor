"""Utility classes and functions"""
import asyncio
from asyncio import Task
from typing import Coroutine


class TaskManager:
    """ "Manager of tasks"""

    def __init__(self) -> None:
        self.__is_context = False
        self._tasks: set[Task] = set()

    def create_task(self, name: str, coro: Coroutine) -> Task:
        """
        Create a task and manage its lifecycle. This uses asyncio.create_task
        internally.

        It will manage the lifecycle to ensure that tasks are cancelled when the
        contest manager is exited and exceptions that were not awaited are logged
        by the app.

        :param name: Name of the task. It should be unique for tracking/tracing
        :param coro: Coroutine to process as a task
        :returns The created task
        :raises RuntimeError when executed outside a context manager

        """
        if not self.__is_context:
            raise RuntimeError("Must be run via context manager")

        task = asyncio.create_task(coro, name=name)
        task.add_done_callback(self._done_callback_handler)
        self._tasks.add(task)
        return task

    def _done_callback_handler(self, task: Task):
        self._tasks.remove(task)

    def __enter__(self):
        self.__is_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for task in self._tasks:
            task.cancel("App task manager context exit")
