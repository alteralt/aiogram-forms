from typing import TYPE_CHECKING, Type, Union, Any

from aiogram.dispatcher.filters.state import StatesGroup, State

from aiogram_forms.const import STATES_GROUP_SUFFIX

if TYPE_CHECKING:
    from aiogram_forms.forms import Form
    from aiogram_forms.menu import Menu


def build_states_group_type(entity: Union[Type['Form'], Type['Menu']]) -> Type[StatesGroup]:
    return type(  # noqa
        f'{entity.__name__}{STATES_GROUP_SUFFIX}',
        (StatesGroup,),
        {
            field_name: State()
            for field_name in entity.get_fields()
        }
    )
