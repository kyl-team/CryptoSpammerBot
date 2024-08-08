from .models import WorkResult
from .utils import format_date


def format_report(results: WorkResult) -> str:
    timestamp = format_date()
    markdown_content = f'# Отчет о работе {timestamp}\n'

    for result in results:
        markdown_content += f'## Канал @{result.name} [{result.id}], беседа: {"есть" if result.has_linked_chat else "нет"}\n\n'
        markdown_content += f'Обработчик: {result.client_name}, прокси: {result.client_proxy["hostname"]}:{result.client_proxy["port"]}\n\n'

        if len(result.errors):
            markdown_content += '### Ошибки\n'
            for error in result.errors:
                markdown_content += f' * {error}\n'

        if len(result.members):
            markdown_content += '### Участники\n'
            i = 0
            for member in result.members:
                markdown_content += f'{i}. @{member.username} ({member.first_name} {member.last_name}), телефон: {member.phone}, био: "{member.bio}", найдено бесед: {len(member.chats)} [{member.id}]\n'
                for chat in member.chats:
                    markdown_content += f'    Беседа @{chat.username}, участников: {len(chat.members)}\n'
                    j = 0
                    for chat_member in chat.members:
                        markdown_content += f'        {j}. Участник @{chat_member.username} ({chat_member.first_name} {chat_member.last_name}), телефон: {chat_member.phone} [{chat_member.id}]\n'
                        j += 1
                i += 1
    return markdown_content
