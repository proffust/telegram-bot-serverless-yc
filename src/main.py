"""
Telegram bot for interacting with Yandex Cloud models (chat, image generation, voice messages).
Uses Yandex Cloud Functions (HTTP trigger) and
Yandex Object Storage for storing conversation contexts.
"""
import os
import json
import logging
import re
from boto3 import session as boto3_session

from telegram.ext import (
    Dispatcher,
    MessageHandler,
    Filters,
    CommandHandler,
)
from telegram import ParseMode, Update, Bot

from speechkit import model_repository, configure_credentials, creds
from speechkit.stt import AudioProcessingType
from pydub import AudioSegment
from yandex_cloud_ml_sdk import YCloudML
from openai import OpenAI

from utils import (
    send_typing_action,
    send_image_action,
    send_speech_action,
    split_markdown_message_safe,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BUCKET = os.environ["CONVERSATION_BUCKET"]
YANDEX_CLOUD_FOLDER = os.environ.get("YANDEX_CLOUD_FOLDER")

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True) # type: ignore[reportCallIssue]

session = boto3_session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)

client_openai = OpenAI(
    base_url="https://llm.api.cloud.yandex.net/v1"
)

AVAILABLE_MODELS = json.loads(os.environ["AVAILABLE_MODELS"])

def load_model_and_msgs(user_id):
    """Load user's model and message history from S3."""
    try:
        file_list = s3.list_objects(Bucket=BUCKET)['Contents']
    except KeyError:
        file_list = [{"Key":"0"}]
    if user_id in [int(f['Key']) for f in file_list]:
        user_context = json.loads(s3.get_object(Bucket=BUCKET,
                                                Key=str(user_id))['Body'].read().decode('utf-8'))
        model_name = user_context['model']
        msgs = user_context["messages"]
    else:
        model_name = "yandexgpt"
        msgs = []
        s3.put_object(Bucket=BUCKET,
                      Key=str(user_id),
                      Body=b'{"model": "yandexgpt", "messages": []}')
    return model_name, msgs

@send_typing_action
def start(update: Update, _):
    """Send a welcome message when the /start command is issued."""
    update.message.reply_text("Привет! Я бот для общения с моделями Яндекс.Облака.")

@send_typing_action
def clear_context(update: Update, _):
    """Clear the conversation context for the user."""
    model_name, _ = load_model_and_msgs(update.message.from_user.id)
    user_context = {"model": model_name, "messages": []}
    s3.put_object(Bucket=BUCKET,
                  Key=str(update.message.from_user.id),
                  Body=json.dumps(user_context).encode('utf-8'))
    update.message.reply_text("Контекст очищен.")

@send_typing_action
def process_message(update: Update, context):
    """Process a text message from the user."""
    chat_id = update.message.chat_id
    model_name, msgs = load_model_and_msgs(update.message.from_user.id)
    msgs.append({"role": "user", "content": update.message.text})
    response = client_openai.chat.completions.create(
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/{model_name}/latest",
        messages=msgs
    )
    message = response.choices[0].message.content or ""
    if message:
        msgs.append({"role": "assistant", "content": message})
        user_context = {"model": model_name, "messages": msgs}
        s3.put_object(Bucket=BUCKET,
                    Key=str(update.message.from_user.id),
                    Body=json.dumps(user_context).encode('utf-8'))
        chunks = split_markdown_message_safe(message)
        for chunk in chunks:
            context.bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN_V2
            )

@send_typing_action
def get_model(update: Update, _):
    """Get the current model for the user."""
    model_name, _ = load_model_and_msgs(update.message.from_user.id)
    update.message.reply_text(f"Текущая модель: {model_name}")

@send_typing_action
def set_model(update: Update, context):
    """Set a new model for the user."""
    if len(context.args) != 1:
        update.message.reply_text("Использование: /set_model <model_name>," \
                                  " где model_name - одна из доступных моделей: "
                                  + ", ".join(AVAILABLE_MODELS))
        return
    model_name = context.args[0]

    if model_name not in AVAILABLE_MODELS:
        update.message.reply_text(f"Модель {model_name} недоступна." \
                                  " Доступные модели: " + ", ".join(AVAILABLE_MODELS))
        return
    _, msgs = load_model_and_msgs(update.message.from_user.id)
    user_context = {"model": model_name, "messages": msgs}
    s3.put_object(Bucket=BUCKET,
                  Key=str(update.message.from_user.id),
                  Body=json.dumps(user_context).encode('utf-8'))
    update.message.reply_text(f"Модель установлена на: {model_name}")

@send_image_action
def generate_image(update: Update, context):
    """Generate an image based on a text prompt."""
    if update.effective_chat is not None:
        sdk = YCloudML(
            folder_id=YANDEX_CLOUD_FOLDER,
        )
        text = update.message.text
        model = sdk.models.image_generation("yandex-art")
        match_obj = re.match(r"^/image(.*)", text)
        prompt = match_obj[1].strip() if match_obj and match_obj[1] else ""
        if not prompt:
            update.message.reply_text("Использование: /image <текстовый запрос>")
        operation = model.run_deferred(prompt)
        result = operation.wait()
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=result.image_bytes,
        )

def handle_photo(update: Update, _):
    """Handle photo messages (not implemented)."""
    update.message.reply_text("Обработка фото не реализована.")

@send_speech_action
def process_voice_message(update: Update, context):
    """Process a voice message from the user."""
    if update.message.voice:
        file_id = update.message.voice.file_id
    else:
        file_id = update.message.audio.file_id
    chat_id = update.message.chat_id
    file = bot.get_file(file_id)
    file.download("/tmp/voice_message.ogg")
    model_stt = model_repository.recognition_model()

    # Настройки распознавания
    model_stt.model = 'general'
    model_stt.language = 'ru-RU'
    model_stt.audio_processing_type = AudioProcessingType.Full

    try:
        result = model_stt.transcribe_file("/tmp/voice_message.ogg")
        speech_text = ' '.join([str(res.normalized_text) for res in result])
    except Exception as e: # pylint: disable=broad-except
        update.message.reply_text(f"Не удалось распознать сообщение: {e}")
    model_name, msgs = load_model_and_msgs(update.message.from_user.id)
    msgs.append({"role": "user", "content": speech_text})
    response = client_openai.chat.completions.create(
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/{model_name}/latest",
        messages=msgs
    )
    message = response.choices[0].message.content or ""
    if message:
        msgs.append({"role": "assistant", "content": message})
        user_context = {"model": model_name, "messages": msgs}
        s3.put_object(Bucket=BUCKET,
                    Key=str(update.message.from_user.id),
                    Body=json.dumps(user_context).encode('utf-8'))
        model_tts = model_repository.synthesis_model()
        result = model_tts.synthesize(message, raw_format=False)
        if isinstance(result, AudioSegment):
            result.export("/tmp/generated_voice.ogg", 'ogg')
        context.bot.send_message(
            chat_id=chat_id,
            text=f"Вы сказали: {speech_text}"
        )
        with open("/tmp/generated_voice.ogg", 'rb') as voice:
            context.bot.send_voice(chat_id=chat_id, voice=voice)
        chunks = split_markdown_message_safe(message)
        for chunk in chunks:
            context.bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN_V2
            )

@send_typing_action
def unknown_command(update: Update, _):
    """Handle unknown commands."""
    update.message.reply_text("Неизвестная команда. Используйте /help для списка команд.")

@send_typing_action
def send_help(update: Update, _):
    """Send a help message listing available commands."""
    help_text = (
        "/start - Начать общение с ботом\n"
        "/new_session - Очистить контекст общения\n"
        "/set_model <model_name> - Установить модель для общения\n"
        "/get_model - Показать текущую модель\n"
        "/image <текстовый запрос> - Сгенерировать изображение по текстовому запросу\n"
        "Вы также можете отправлять голосовые сообщения, и я отвечу вам голосом!"
    )
    update.message.reply_text(help_text)

# Точка входа Yandex Cloud Function (HTTP trigger)
def handler(event, context):
    """Handle incoming HTTP requests from Yandex Cloud Functions."""
    iam_token = context.token.get("access_token")
    configure_credentials(
        yandex_credentials=creds.YandexCredentials(
            iam_token=iam_token
        )
    )
    body = event.get("body") if isinstance(event, dict) else event
    if not body:
        return {"statusCode": 400, "body": json.dumps({"error": "empty body"})}

    try:
        update_json = json.loads(body) if isinstance(body, str) else body
    except json.JSONDecodeError as e:
        logger.exception("Bad JSON: %s", e)
        return {"statusCode": 400, "body": json.dumps({"error": "bad json"})}


    dispatcher.add_handler(CommandHandler("new_session",clear_context))
    dispatcher.add_handler(CommandHandler("start",start))
    dispatcher.add_handler(CommandHandler("help",send_help))
    dispatcher.add_handler(CommandHandler("set_model",set_model))
    dispatcher.add_handler(CommandHandler("get_model",get_model))
    dispatcher.add_handler(CommandHandler("image", generate_image))
    #dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))
    dispatcher.add_handler(MessageHandler(Filters.voice, process_voice_message))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))

    try:
        dispatcher.process_update(Update.de_json(update_json, bot))
    except Exception as e: # pylint: disable=broad-except
        logger.exception("Error processing update: %s", e)
        return {"statusCode": 500}

    return {"statusCode": 200}
