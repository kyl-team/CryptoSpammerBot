import json
import os
from abc import ABC

import aiofiles
from pydantic import BaseModel


class BaseStorage(BaseModel, ABC):
    def __init__(self):
        if os.path.exists(self.pathname):
            with open(self.pathname, 'r', encoding='utf-8') as f:
                super().__init__(**json.load(f))
        else:
            super().__init__()
            with open(self.pathname, 'w', encoding='utf-8') as f:
                json.dump(self.model_dump(), f, sort_keys=True, indent=4, ensure_ascii=True)

    @property
    def pathname(self):
        raise NotImplementedError('Child class must implement `pathname`')

    async def save(self):
        async with aiofiles.open(self.pathname, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.model_dump(), ensure_ascii=True, sort_keys=True, indent=4))
