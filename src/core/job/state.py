from enum import Enum

from pydantic import BaseModel


class JobPhase(str, Enum):
    SIMILAR = 'SIMILAR'
    JOIN_CHANNELS = 'JOIN_CHANNELS'
    SUBSCRIBERS = 'SUBSCRIBERS'
    SUBSCRIBERS_SEARCH = 'SUBSCRIBERS_SEARCH'
    JOIN_CHATS = 'JOIN_CHATS'
    CHAT_MEMBERS = 'CHAT_MEMBERS'
    MESSAGES_SEND = 'MESSAGES_SEND'
    FINISHED = 'FINISHED'


class KnownUser(BaseModel):
    user_id: int
    username: str | None


class JobState(BaseModel):
    known_users: list[KnownUser] | None = None
    running: bool = False
    phase: JobPhase | None = None

    def start(self):
        if not self.running:
            raise ValueError("Job state is already running")

        self.running = True
        self.known_users = []

    def stop(self):
        if not self.running:
            raise ValueError("Job state is not running")

        self.running = False

    def clear(self):
        super().__init__()

    @property
    def running_string(self) -> str:
        return 'завершен' if self.phase == JobPhase.FINISHED else ('в процессе' if self.running else 'остановлен')


current = JobState()
