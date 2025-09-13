
resource "telegram_bot_webhook" "webhook" {
  url = "https://functions.yandexcloud.net/${yandex_function.ai-bot-function.id}"
  depends_on = [
    yandex_function.ai-bot-function,
  ]
}


resource "telegram_bot_commands" "ai-bot-commands" {
  commands = [
    {
      command = "start",
      description = "Поздороваться"
    },
    {
      command = "image",
      description = "Генерация изображения по текстовому промпту"
    },
    {
      command = "new_session",
      description = "Начать новый сеанс общения с ботом"
    },
    {
      command = "get_model",
      description = "Вывод текущей используемой модели"
    },
    {
      command = "set_model",
      description = "Установка модели для общения с ботом"
    },
    {
      command = "help",
      description = "Помощь по командам бота"
    }
  ]
}