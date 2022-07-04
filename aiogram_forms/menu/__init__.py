from collections import OrderedDict
from typing import TYPE_CHECKING, Mapping, Type, Optional, Union, Any, Coroutine

from aiogram_forms.base import Entity
from aiogram_forms.dispatcher import MenuDispatcher
from aiogram_forms.enums import EntityType

if TYPE_CHECKING:
    from aiogram_forms.forms import Form


class MenuItem:
    key: str

    _label: str
    _action: Optional[Union[Type['Menu'], Type['Form'], Coroutine[Any, Any, None]]]
    _link: Optional[str]

    def __init__(
            self,
            label: str,
            action: Optional[Union[Type['Menu'], Type['Form'], Coroutine[Any, Any, None]]] = None,
            link: Optional[str] = None
    ):
        self._label = label
        self._action = action
        self._link = link

    def __set_name__(self, owner: Type['Menu'], name: str) -> None:
        self.key = name

    @property
    def label(self) -> str:
        return self._label


class Menu(Entity):
    type: EntityType = EntityType.Menu

    _items = {}

    def __init_subclass__(cls, name: str = None) -> None:
        cls.id = name or cls.__name__
        cls._items = Menu._get_form_fields_map(cls)
        MenuDispatcher.register(cls)

    @staticmethod
    def _get_form_fields_map(cls) -> Mapping[str, 'MenuItem']:
        return OrderedDict({
            name: item
            for name, item in cls.__dict__.items()
            if isinstance(item, MenuItem)
        })

    @classmethod
    def get_fields(cls):  # TODO: rename to get_children
        return cls._items
