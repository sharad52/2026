from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, ForeignKey

Base = declarative_base()

class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float)
