from aiogram import executor, types
from aiogram.types import ReplyKeyboardRemove

from aiogram_forms import forms, menu, FormsDispatcher
from aiogram_forms.dispatcher import Store, MenuDispatcher

from examples import get_translation as _, dp


class MainMenu(menu.Menu, name='main'):
    settings = menu.MenuItem('Settings', link='name-form')
    about = menu.MenuItem('About', link='about')  # TODO: resolve imports


class AboutMenu(menu.Menu, name='about'):
    version = menu.MenuItem('Version')
    back = menu.MenuItem('Back', link='main')


class NameForm(forms.Form, name='name-form'):
    name = forms.StringField(_('Name'), required=True)
    second = forms.StringField('Age')


async def on_form_complete() -> None:
    print(await Store.get_form_data(NameForm))
    await dp.bot.send_message(
        types.Chat.get_current().id,
        text='Saved.',
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message_handler(commands='start')
async def command_start(message: types.Message):
    await FormsDispatcher.start(NameForm, callback=on_form_complete())


@dp.message_handler(commands='menu')
async def command_start(message: types.Message):
    await MenuDispatcher.show(MainMenu)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
