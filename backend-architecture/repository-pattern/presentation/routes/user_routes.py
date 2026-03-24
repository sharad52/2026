from fastapi import APIRouter, Depends
from application.user.create_user import CreateUserUseCase
from presentation.dependencies import get_uow

router = APIRouter()

@router.post("/users")
async def create_user(name: str, uow=Depends(get_uow)):
    use_case = CreateUserUseCase(uow)
    return await use_case.execute(name)
