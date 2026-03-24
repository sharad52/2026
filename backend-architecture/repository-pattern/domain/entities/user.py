"""User entity"""

class User:
    def __init__(self, id:int | None, name: str):
        self.id = id
        self.name = name

