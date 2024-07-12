from pydantic import BaseModel

from lib import BaseStorage


class JobMessage(BaseModel):
    text: str = ''


class JobStorage(BaseStorage):
    similar: bool = True
    message: JobMessage = JobMessage()

    @property
    def pathname(self):
        return 'data/job.json'


storage = JobStorage()
