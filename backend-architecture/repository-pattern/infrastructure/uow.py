from domain.uow import UnitOfWork
from infrastructure.repositories.user_repo import UserRepositoryImpl
from infrastructure.repositories.account_repo import AccountRepositoryImpl


REPO_REGISTRY = {
    UserRepositoryImpl: UserRepositoryImpl,
    AccountRepositoryImpl: AccountRepositoryImpl,
}

class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._repos = {}

    async def __aenter__(self):
        self.session = self.session_factory()
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    def get_repository(self, repo_type):
        if repo_type not in self._repos:
            self._repos[repo_type] = repo_type(self.session)
        return self._repos[repo_type]