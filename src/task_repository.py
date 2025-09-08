from typing import List

from db import engine, tasks
from task import Task


class TaskRepository:
    def add_task(self, text: str) -> int:
        query = tasks.insert().values(text=text, parent_id=-1)

        with engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.inserted_primary_key[0]

    def get_list(self, is_done: bool = None) -> List[Task]:
        query = tasks.select()

        if is_done is not None:
            query = query.where(tasks.c.is_done == is_done)

        with engine.connect() as conn:
            return [
                Task(id=id, text=text, is_done=is_done, parent_id=parent_id)
                for id, text, is_done, parent_id in conn.execute(
                    query.order_by(tasks.c.id)
                )
            ]

    def find_tasks(self, needle: str) -> List[Task]:
        query = tasks.select().where(tasks.c.text.ilike(f"%{needle}%"))

        with engine.connect() as conn:
            return [
                Task(id=id, text=text, is_done=is_done, parent_id=parent_id)
                for id, text, is_done, parent_id in conn.execute(
                    query.order_by(tasks.c.id)
                )
            ]

    def finish_tasks(self, ids: List[int]) -> None:
        query = tasks.update().where(tasks.c.id.in_(ids)).values(is_done=True)
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()

    def reopen_tasks(self, ids: List[int]) -> None:
        query = tasks.update().where(tasks.c.id.in_(ids)).values(is_done=False)
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()

    def clear(self, is_done: bool = None) -> None:
        query = tasks.delete()

        if is_done is not None:
            query = query.where(tasks.c.is_done == is_done)

        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
