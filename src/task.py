from dataclasses import dataclass


@dataclass
class Task:
    id: int
    text: str = ""
    is_done: bool = False
    parent_id: int = -1
    level = 0

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        status = "Done!" if self.is_done else "In progress"
        return f"{self.id}: {self.text} Status: {status}"
