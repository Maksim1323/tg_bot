from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    waiting_text_for_translate = State()
    waiting_photo_for_ocr = State()
    waiting_task_description = State()
    waiting_task_files = State()
