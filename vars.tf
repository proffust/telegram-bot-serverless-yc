variable cloud_id {
  type        = string
  default     = ""
  description = "ID of your cloud in YC"
}

variable folder_id {
  type        = string
  default     = ""
  description = "ID of your folder in YC"
}

variable conversation_bucket_prefix {
  type        = string
  default     = "telegram-bot-conversation"
  description = "Prefix for conversation bucket name. to prefix add folder id"
}

variable bot_token {
  type        = string
  sensitive   = true
  default     = ""
  description = "Telegram bot token"
}

variable available_models_yandex {
  type = list(string)
  default = []
  description = "Available models for yandex ML API"
}

variable available_models_sber {
  type = list(string)
  default = []
  description = "Available models for Sber API"
}

variable "gigachat_auth" {
  type = string
  default = ""
  description = "Auth token for Sber Gigachat"
}