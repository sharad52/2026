from __future__ import annotations

from abc import ABC, abstractmethod


class AccountRepository(ABC):

    @abstractmethod
    async def add(self, account): pass
