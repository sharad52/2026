from __future__ import annotations


class Account:
    """Account entities"""

    def __init__(self, id: int | None, user_id: int, balance: float):
        self.id = id
        self.user_id = user_id
        self.__balance = balance

    @property
    def balance(self) -> None:
        return self.__balance
    
    def deposit(self, amount: float) -> None:
        self.__validate_amount(amount)
        self.__balance += amount

    def withdraw(self, amount: float) -> None:
        self.__validate_amount(amount)
        if amount > self.__balance:
            raise ValueError("Insufficient balance")
        self.__balance -= amount
    
    def __validate_amount(self, amount: float):
        if amount <= 0:
            raise ValueError("Amount must be positive")
 