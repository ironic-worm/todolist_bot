import typing

from aiogram import Bot, Dispatcher, types
from aiogram.utils.callback_data import CallbackData

from settings import settings
from task import Task
from task_repository import TaskRepository

bot = Bot(token=settings["TELEGRAM_TOKEN"])
dispatcher = Dispatcher(bot)
clear_cb = CallbackData("clear", "action")

tasks = []

_repository = TaskRepository()


def _set_tasks_level(tasks: typing.List[Task]):

    for num2, task in enumerate(tasks):
        if task.parent_id != -1:
            for num in range(num2 - 1, -1, -1):
                if tasks[num].id == task.parent_id:
                    task.level = tasks[num].level + 1


def _sort_tasks(tasks: typing.List[Task], id_t: int):

    tasks_copy = []
    for task in tasks:
        if task.parent_id == id_t:
            tasks_copy.append(task)
            id_new = task.id
            new_task = _sort_tasks(tasks, id_new)
            for n_t in new_task:
                tasks_copy.append(n_t)
    return tasks_copy


def _tasks_done(tasks: typing.List[Task], task_ids: typing.List[int]):

    done_ids = []
    for t_id in task_ids:
        for task in tasks:
            if task.parent_id == t_id:
                done_ids.append(task.id)
                id_new = [task.id]
                new_ids = _tasks_done(tasks, id_new)
                for n_i in new_ids:
                    done_ids.append(n_i)
    return done_ids


def _task_dto_to_string(task: Task) -> str:
    status_char = "\u2705" if task.is_done else "\u274c"
    child = (
        "" if task.parent_id == -1 else "  " * task.level
    )  # добавляем пробелы в зависимости от уровня вложенности задания
    return f"{child}{task.id}: {task.text} | {status_char}"


def _get_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton(
            "Удалить все!", callback_data=clear_cb.new(action="all")
        ),
        types.InlineKeyboardButton(
            "Только завершенные", callback_data=clear_cb.new(action="completed")
        ),
    )


@dispatcher.message_handler(commands=["todo"])
async def create_task(message: types.Message):
    text = (message.get_args() or "").strip()
    if not text:
        await message.reply("Укажите текст задачи: /todo <текст>")
        return
    task_pk = _repository.add_task(text)
    task_id = task_pk[0] if isinstance(task_pk, (list, tuple)) else int(task_pk)
    await message.reply(f"Задача добавлена: {task_id}")


@dispatcher.message_handler(commands=["list"])
async def get_list(message: types.Message):
    if message.get_args():
        tasks = _repository.get_list(message.get_args())
    else:
        tasks = _repository.get_list()
    _set_tasks_level(tasks)
    tasks = _sort_tasks(tasks, -1)
    if tasks:
        text = "\n".join([_task_dto_to_string(res) for res in tasks])
    else:
        text = "У вас нет задач!"
    await bot.send_message(message.chat.id, text)


@dispatcher.message_handler(commands=["find"])
async def find_tasks(message: types.Message):
    query = (message.get_args() or "").strip()
    if not query:
        await bot.send_message(
            message.chat.id, "Укажите текст для поиска: /find <слово|фраза>"
        )
        return
    tasks = _repository.find_tasks(query)
    if tasks:
        text = "\n".join([_task_dto_to_string(res) for res in tasks])
    else:
        text = 'Задачи по условию "' + query + '" не найдены!'
    await bot.send_message(message.chat.id, text)


@dispatcher.message_handler(commands=["done"])
async def finish_task(message: types.Message):
    try:
        task_ids = [int(id_) for id_ in message.get_args().split(" ")]
        _repository.finish_tasks(task_ids)
        tasks = _repository.get_list()
        subtasks = _tasks_done(tasks, task_ids)
        _repository.finish_tasks(subtasks)
        if len(subtasks) > 0:
            text = f"Завершенные задачи: {task_ids} и подзадачи: {subtasks}"
        else:
            text = f"Завершенные задачи: {task_ids}"
    except ValueError as e:
        text = "Неправильный номер задачи"

    await message.reply(text)


@dispatcher.message_handler(commands=["reopen"])
async def reopen_task(message: types.Message):
    arg = (message.get_args() or "").strip()
    if not arg:
        await message.reply("Укажите id задачи: /reopen <id>")
        return
    try:
        task_id = int(arg)
    except ValueError:
        await message.reply("Некорректный id. Нужен целый номер задачи.")
        return

    if hasattr(_repository, "reopen"):
        result = _repository.reopen(task_id)
        await message.reply(
            "Задача с таким id не найдена."
            if result == "not_found"
            else (
                "Задача уже открыта."
                if result == "already_open"
                else "Задача переоткрыта."
            )
        )
    else:

        _repository.reopen_tasks([task_id])
        await message.reply("Задача переоткрыта.")


@dispatcher.message_handler(commands=["clear"])
async def clear(message: types.Message):
    await message.reply("Вы хотите удалить ваши задачи?", reply_markup=_get_keyboard())


@dispatcher.callback_query_handler(clear_cb.filter(action=["all", "completed"]))
async def callback_clear_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]
):
    await query.answer()
    callback_data_action = callback_data["action"]

    if callback_data_action == "all":
        _repository.clear()
    else:
        _repository.clear(is_done=True)

    await bot.edit_message_text(
        f"Задачи удалены! ",
        query.from_user.id,
        query.message.message_id,
    )


@dispatcher.message_handler(commands=["help", "start"])
async def create_task(message: types.Message):
    await message.reply(
        "ToDo бот - менеджер задач.\n\n"
        + '/todo - наберите команду и описание задачи и она добавится в список. Например: "/todo найти носки"\n\n'
        + '/list - покажет список задач и их номера "/list True" или "/list False" покажет завершенные и не завершенные задачи соответственно\n\n'
        + '/find - поиск задачи по ключевому слову. Например: "/find найти" покажет задачи в которых упоминается слово найти\n\n'
        + '/done - команда и номер задачи отметит задачу и подзадачи как выполненные. Например: "/done 1 3" - команда отметит выполненными задания 1 и 3 и их подзадачи\n\n'
        + '/reopen - переоткрыть задачу. Например: "/reopen 1"\n\n'
        + "/clear - удаление задач, всех или только выполненных"
    )
