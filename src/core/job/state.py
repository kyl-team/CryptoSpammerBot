from pydantic import BaseModel


class KnownUser(BaseModel):
    user_id: int
    username: str | None


class JobState(BaseModel):
    known_users: list[KnownUser] | None = None
    running: bool = False

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
        return 'в процессе' if self.running else 'остановлен'


current = JobState()
