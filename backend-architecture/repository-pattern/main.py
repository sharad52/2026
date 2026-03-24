from fastapi import FastAPI
from presentation.routes.user_routes import router as user_router
from presentation.routes.account_routes import router as account_router

app = FastAPI()

app.include_router(user_router)
app.include_router(account_router)