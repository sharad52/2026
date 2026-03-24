from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type, TypeVar


T = TypeVar("T")

class UnitOfWork(ABC):

    @abstractmethod
    async def __aenter__(self): pass

    @abstractmethod
    async def __aexit__(self, *args): pass

    @abstractmethod
    async def commit(self): pass

    @abstractmethod
    async def rollback(self): pass

    @abstractmethod
    def get_repository(self, repo_type: Type[T]) -> T:
        pass
