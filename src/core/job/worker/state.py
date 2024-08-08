from datetime import datetime, timedelta

from aiogram.types import Message


class TaskState:
    def __init__(self, message: Message, total: int):
        self.message = message
        self.total = total
        self.known_discussions = set()
        self.progress = 0
        self.state = None
        self.last_print = None

    async def sync(self):
        if self.last_print is None or datetime.now() > self.last_print + timedelta(seconds=10):
            state_text = f", {self.state}" if self.state else ""
            await self.message.edit_text(f'⌛ Обработано: {self.progress}/{self.total}{state_text}')
            self.last_print = datetime.now()

    async def start_channel(self):
        self.progress += 1
        self.state = None
        await self.sync()

    async def set_state(self, state: str):
        self.state = state
        await self.sync()
