from domain.entities.account import Account
from infrastructure.repositories.account_repo import AccountRepositoryImpl


class CreateAccountUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, user_id: int, balance: float):

        async with self.uow as uow:
            repo = uow.get_repository(AccountRepositoryImpl)

            account = Account(id=None, user_id=user_id, balance=balance)
            await repo.add(account)

            await uow.commit()
            return account
