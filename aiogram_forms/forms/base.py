"""
Base classes for all components
"""
import abc
from collections import OrderedDict
from typing import Type, Mapping, Union, Callable, Optional

from aiogram_forms.base import Entity
from aiogram_forms.dispatcher import FormsDispatcher
from aiogram_forms.enums import EntityType


class BaseValidator(abc.ABC):  # pylint: disable=too-few-public-methods
    """
    Base validator class
    """

    @abc.abstractmethod
    async def validate(self, value: str) -> bool:
        """
        Validate value provided by user
        :param value: user input
        :return: bool
        """


class Field(abc.ABC):
    """
    Base field class
    """
    key: str
    form: Type['Form']

    _label: Union[str, Callable[..., str]]
    _required: bool

    def __init__(
            self,
            label: Union[str, Callable[..., str]],
            required: bool = False
    ):
        self._label = label
        self._required = required

    def __set_name__(self, owner: Type['Form'], name: str) -> None:
        self.form = owner
        self.key = name

    @property
    def label(self) -> str:
        return self._label if isinstance(self._label, str) else self._label()


class Form(Entity):
    """
    Base form class
    """
    type: EntityType = EntityType.Form

    _fields: Mapping[str, 'Field']

    def __init_subclass__(cls, name: str = None) -> None:
        cls.id = name or cls.__name__
        cls._fields = Form._get_form_fields_map(cls)
        FormsDispatcher.register(cls)

    @staticmethod
    def _get_form_fields_map(cls) -> Mapping[str, 'Field']:
        return OrderedDict({
            name: item
            for name, item in cls.__dict__.items()
            if isinstance(item, Field)
        })

    @classmethod
    def get_fields(cls) -> Mapping[str, 'Field']:
        return cls._fields

    @classmethod
    def get_next_field(cls, field: 'Field') -> Optional['Field']:
        keys = list(cls._fields.keys())
        index = keys.index(field.key)

        if index + 1 < len(keys):
            return cls._fields[keys[index + 1]]
        return None

    @classmethod
    def get_first_field(cls) -> 'Field':
        return cls._fields[list(cls._fields.keys())[0]]
