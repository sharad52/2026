from fastapi import APIRouter, Depends
from application.account.create_account import CreateAccountUseCase
from presentation.dependencies import get_uow

router = APIRouter()

@router.post("/accounts")
async def create_account(user_id: int, balance: float, uow=Depends(get_uow)):
    use_case = CreateAccountUseCase(uow)
    return await use_case.execute(user_id, balance)