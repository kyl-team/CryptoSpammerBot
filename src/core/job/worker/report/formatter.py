from .models import WorkResult, ChatResult, UserResult, ChannelResult
from .utils import format_date


def format_member(result: UserResult, index: int) -> str:
    content = ''
    content += f'{index}. @{result.username} ({result.first_name} {result.last_name}), телефон: {result.phone}, био: "{result.bio}", найдено бесед: {len(result.chats)} [{result.id}]\n'
    for chat in result.chats:
        content += format_chat(chat)
    return content


def format_chat(result: ChatResult):
    content = f'## Чат @{result.username} [{result.id}, {result.depth}]\n'

    if len(result.errors):
        content += f'### Ошибки\n'
        for error in result.errors:
            content += f' * {error}\n'

    content += f'### Чаты\n'
    i = 0
    for member in result.members:
        content += format_member(member, i)
        i += 1

    return content


def format_channel(result: ChannelResult) -> str:
    content = ''

    content += f'# Канал @{result.name} [{result.id}], беседа: {"есть" if result.linked_chat is not None else "нет"}\n\n'
    content += f'Обработчик: {result.client_name}, прокси: {result.client_proxy["hostname"]}:{result.client_proxy["port"]}\n\n'

    if len(result.errors):
        content += '### Ошибки\n'
        for error in result.errors:
            content += f' * {error}\n'

    if result.linked_chat:
        content += format_chat(result.linked_chat)

    return content


def format_report(results: WorkResult) -> str:
    timestamp = format_date()
    markdown_content = f'# Отчет о работе {timestamp}\n'

    for result in results:
        markdown_content += format_channel(result)

    return markdown_content
