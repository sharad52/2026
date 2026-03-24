from infrastructure.uow import SqlAlchemyUnitOfWork
from infrastructure.db.session import AsyncSessionLocal

def get_uow():
    return SqlAlchemyUnitOfWork(AsyncSessionLocal)
