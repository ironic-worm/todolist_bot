from aiogram import executor

from db import init_db
from todo_list_bot import dispatcher

if __name__ == "__main__":

    init_db()
    executor.start_polling(dispatcher, skip_updates=True)
