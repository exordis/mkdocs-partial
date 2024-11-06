from abc import ABC
from typing import Any, Callable, Dict


class TemplaterExtension(ABC):

    def __init__(self, **kwargs):
        self.__args = kwargs
        super().__init__()

    @property
    def filters(self) -> Dict[str, Callable]:
        return {}

    @property
    def args(self) -> Dict[str, Any]:
        return self.__args
