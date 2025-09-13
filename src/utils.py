from functools import wraps
import re
from telegram import ChatAction

def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING
        )
        return func(update, context, *args, **kwargs)

    return command_func

def send_image_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_PHOTO
        )
        return func(update, context, *args, **kwargs)

    return command_func

def send_speech_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.RECORD_VOICE
        )
        return func(update, context, *args, **kwargs)

    return command_func

def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы MarkdownV2 в тексте.
    """
    # Экранируем специальные символы MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r'\\\1', text)

def split_markdown_message_safe(message: str, max_len: int = 4096) -> list:
    """
    Разбивает сообщение на части, сохраняя целостность код-блоков
    и экранируя Markdown-символы вне код-блоков.
    Для код-блоков добавляет правильный синтаксис MarkdownV2.
    """
    lines = message.split("\n")
    chunks = []
    current_chunk = ""
    inside_code_block = False

    for line in lines:
        if line.strip().startswith("```") or line.strip().startswith("~~~"):
            if not inside_code_block:
                # Начало блока кода
                inside_code_block = True
                processed_line = "```\n"  # MarkdownV2 корректный старт
            else:
                # Конец блока кода
                inside_code_block = False
                processed_line = "```\n"
        else:
            # Экранируем только вне блока кода
            processed_line = line if inside_code_block else escape_markdown_v2(line)

        if len(current_chunk) + len(processed_line) + 1 <= max_len:
            current_chunk += processed_line + "\n"
        else:
            if inside_code_block:
                current_chunk += "```\n"
                chunks.append(current_chunk.rstrip("\n"))
                current_chunk = "```\n" + processed_line + "\n"
            else:
                chunks.append(current_chunk.rstrip("\n"))
                current_chunk = processed_line + "\n"

    if current_chunk.strip():
        if inside_code_block:
            current_chunk += "```\n"
        chunks.append(current_chunk.rstrip("\n"))

    return chunks