
from domain.entities.user import User
from infrastructure.db.models.user_model import UserModel

class UserRepositoryImpl:

    def __init__(self, session):
        self.session = session

    async def add(self, user: User):
        user_obj = UserModel(name = user.name)
        self.session.add(user_obj)
        await self.session.flush()
        user.id = user_obj.id
