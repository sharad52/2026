from __future__ import annotations

from abc import ABC, abstractmethod


class UserRepository(ABC):

    @abstractmethod
    async def add(self, user): pass