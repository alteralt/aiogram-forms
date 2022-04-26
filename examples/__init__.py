import os
from typing import Callable

from aiogram import Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage


def get_translation(key: str) -> Callable[..., str]:
    """
    Translation stub
    :param key: Label to be translated
    :return:
    """
    def translate() -> str:
        return f'{key} (translated)'
    return translate


def get_bot() -> Dispatcher:
    """
    Create basic bot and dispatcher
    :return:
    """
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    return Dispatcher(bot, storage=MemoryStorage())


dp: Dispatcher = get_bot()
