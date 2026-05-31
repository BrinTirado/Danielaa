from typing import Protocol

from pydantic import BaseModel


class NavigationResult(BaseModel):
    succeeded: bool
    message: str
    destination: str | None = None


class Navigator(Protocol):
    def move_to(self, room: str) -> NavigationResult: ...

    def dock(self) -> NavigationResult: ...
