"""
Entity dispatcher.
"""
from typing import Type, MutableMapping, Dict, Any

from aiogram import Dispatcher, Router, types

from .core.entities import EntityContainer
from .core.states import EntityContainerStatesGroup
from .forms import Form, FormsManager
from .middleware import EntityMiddleware


class EntityDispatcher:
    """Entity dispatcher."""
    _registry: MutableMapping[
        str,
        MutableMapping[str, Type['EntityContainer']]
    ] = {}

    _dp: Dispatcher
    _router: Router

    def __init__(self):
        self._router = Router()

    def attach(self, dp: Dispatcher):  # pylint: disable=invalid-name
        """Attach aiogram dispatcher."""
        self._dp = dp
        self._dp.message.middleware(EntityMiddleware(self))

        dp.include_router(self._router)

    def register(self, name: str):
        """Register entity with given name."""
        def wrapper(container: Type[EntityContainer]):
            EntityContainerStatesGroup.bind(container)

            for filter_type, filter_ in container.filters().items():
                getattr(self._router, str(filter_type.value))(filter_)(self._get_entity_container_handler(container))

            if container.__name__ not in self._registry:
                self._registry['forms'] = {}

            self._registry['forms'][name] = container
            return container
        return wrapper

    def get_entity_container(self, container_type: Type[EntityContainer], name: str):
        """Het entity container by name and type."""
        entity_container = self._registry['forms'].get(name)
        if entity_container:
            return entity_container
        raise ValueError(f'There are no entity container with name "{name}" of type "{container_type.__name__}"!')

    def _get_entity_container_handler(self, container: Type['EntityContainer']):
        """Get entity container event handler."""
        async def message_handler(event: types.Message, **data: Dict[str, Any]) -> None:
            """Entity container event handler, redirect to manager."""
            if issubclass(container, Form):
                manager = FormsManager(self, event, data)
                await manager.handle(container)
            else:
                raise RuntimeError(f'Container of type "{container.__class__.__name__}" is not supported!')

        return message_handler