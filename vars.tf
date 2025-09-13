variable cloud_id {
    type = string
}

variable folder_id {
    type = string
}

variable conversation_bucket_name {
  type    = string
  default = "telegram-bot-conversation"
}

variable bot_token {
  type      = string
  sensitive = true
}