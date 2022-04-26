from typing import TYPE_CHECKING, Type, MutableMapping, Set, Coroutine, Optional, List

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram_forms import utils

if TYPE_CHECKING:
    from aiogram.dispatcher.filters.state import StatesGroup
    from aiogram_forms.forms.base import Form, Field
    from aiogram_forms.menu import Menu, MenuItem


class Store:

    @staticmethod
    def _get_form_field_data_key(field: 'Field') -> str:
        return f'{field.form.id}:{field.key}'

    @staticmethod
    def get_state() -> FSMContext:
        return Dispatcher.get_current().current_state()

    @classmethod
    async def save_response(cls, field: 'Field', value: str):
        await cls.get_state().update_data(
            **{
                cls._get_form_field_data_key(field): value
            }
        )

    @classmethod
    async def get_form_data(cls, form: Type['Form']) -> dict:
        """
        Get form data for current user
        :return:
        """
        state = Dispatcher.get_current().current_state()

        fields = form.get_fields().values()
        form_data_keys = (cls._get_form_field_data_key(field) for field in fields)

        async with state.proxy() as data:
            return {
                key.split(':')[-1]: data[key]  # TODO: handle keys
                for key in data
                if key in form_data_keys
            }


class MenuDispatcher:
    _menus: MutableMapping[str, Type['Menu']] = {}
    _state: MutableMapping[str, Type['StatesGroup']] = {}
    _state_item_map: MutableMapping[str, 'MenuItem'] = {}

    @classmethod
    def register(cls, menu: Type['Menu']) -> None:
        if menu.id in cls._menus:
            raise ValueError(f'Menu with name {menu.id} is already registered!')

        cls._state[menu.id] = utils.build_states_group_type(menu)
        cls._menus[menu.id] = menu

        for item, state in zip(menu._items.values(), cls._state[menu.id].states_names):  # noqa
            cls._state_item_map[state] = item

    @classmethod
    async def show(cls, menu: Type['Menu'], message_id: int = None) -> None:
        dispatcher: Dispatcher = Dispatcher.get_current()

        states = [state for state in cls._state[menu.id].states_names]  # TODO
        dispatcher.register_callback_query_handler(cls._handle_callback_query, lambda c: c.data in states)

        if not message_id:
            await dispatcher.bot.send_message(
                types.Chat.get_current().id,
                text=menu.id,
                reply_markup=cls._build_menu_keyboard(menu)
            )
        else:
            await dispatcher.bot.edit_message_text(
                text=menu.id,
                chat_id=types.Chat.get_current().id,
                message_id=message_id
            )
            await dispatcher.bot.edit_message_reply_markup(
                chat_id=types.Chat.get_current().id,
                message_id=message_id,
                reply_markup=cls._build_menu_keyboard(menu)
            )

    @classmethod
    def _build_menu_keyboard(cls, menu: Type['Menu']):
        items: List['MenuItem'] = list(menu.get_fields().values())

        keyboard = InlineKeyboardMarkup()
        for item in items:
            keyboard.add(
                InlineKeyboardButton(item.label, callback_data=getattr(cls._state[menu.id], item.key).state)
            )

        return keyboard

    @classmethod
    async def _handle_callback_query(cls, callback_query: types.CallbackQuery):
        dispatcher: Dispatcher = Dispatcher.get_current()
        await dispatcher.bot.answer_callback_query(callback_query.id)

        item = cls._state_item_map[callback_query.data]
        if isinstance(item._action, str):
            await cls.show(cls._menus[item._action], message_id=callback_query.message.message_id)


class FormsDispatcher:
    _forms: MutableMapping[str, Type['Form']] = {}
    _state: MutableMapping[str, Type['StatesGroup']] = {}

    _state_field_map: MutableMapping[str, 'Field'] = {}
    _registry: Set[str] = set()
    _callbacks: MutableMapping[str, Optional[Coroutine]] = {}

    @classmethod
    def register(cls, form: Type['Form']) -> None:
        if form.id in cls._forms:
            raise ValueError(f'Form with name {form.id} is already registered!')

        cls._state[form.id] = utils.build_states_group_type(form)
        cls._forms[form.id] = form

        for field, state in zip(form._fields.values(), cls._state[form.id].states_names):  # noqa
            cls._state_field_map[state] = field

    @classmethod
    async def start(cls, form: Type['Form'], callback: Optional[Coroutine] = None) -> None:
        if form.id not in cls._registry:
            cls._register_message_handler(form)

        cls._callbacks[form.id] = callback
        await cls._start_field_promotion(form, form.get_first_field())

    @classmethod
    def _register_message_handler(cls, form: Type['Form']) -> None:
        dispatcher: Dispatcher = Dispatcher.get_current()
        dispatcher.register_message_handler(cls._handle_input, state=cls._state[form.id].states)
        cls._registry.add(form.id)

    @classmethod
    async def _handle_input(cls, message: types.Message, state: FSMContext) -> None:
        field = cls._state_field_map[await state.get_state()]

        await Store.save_response(field, message.text)

        next_field = field.form.get_next_field(field)
        if next_field:
            await cls._start_field_promotion(field.form, next_field)
        else:
            await cls.finish(field.form)

    @classmethod
    async def finish(cls, form) -> None:
        state = Dispatcher.get_current().current_state()
        await state.reset_state(with_data=False)

        if cls._callbacks[form.id]:
            await cls._callbacks[form.id]

    @classmethod
    async def _start_field_promotion(cls, form: Type['Form'], field: 'Field') -> None:
        dispatcher = Dispatcher.get_current()
        await dispatcher.current_state().set_state(
            getattr(cls._state[form.id], field.key).state
        )
        await dispatcher.bot.send_message(
            types.Chat.get_current().id,
            text=field.label,
            reply_markup=ReplyKeyboardRemove()
        )
