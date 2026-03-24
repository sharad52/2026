from domain.entities.user import User
from infrastructure.repositories.user_repo import UserRepositoryImpl

class CreateUserUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, name: str):

        async with self.uow as uow:
            repo = uow.get_repository(UserRepositoryImpl)

            user = User(id=None, name=name)
            await repo.add(user)

            await uow.commit()
            return user
