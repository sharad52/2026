from domain.entities.account import Account
from infrastructure.db.models.account_model import AccountModel


class AccountRepositoryImpl:

    def __init__(self, session):
        self.session = session

    async def add(self, account: Account):
        account_obj = AccountModel(
            user_id=account.user_id,
            balance=account.__balance
        )
        self.session.add(account_obj)
        await self.session.flush()
        account.id = account_obj.id
