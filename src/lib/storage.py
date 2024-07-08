import json
import os
from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseStorage(BaseModel, ABC):
    def __init__(self):
        pathname = self.get_pathname()

        if os.path.exists(pathname):
            with open(pathname, 'r', encoding='utf-8') as f:
                super().__init__(**json.load(f))
        else:
            super().__init__()

        with open(pathname, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=True, sort_keys=True, indent=4)

    @abstractmethod
    def get_pathname(self) -> str:
        pass
