terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
      version = "0.156.0"
    }
    telegram = {
      source = "yi-jiayu/telegram"
      version = "0.3.1"
    }
  }
}

provider "yandex" {
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  service_account_key_file = "./authorized_key.json"
}

provider "telegram" {
  bot_token = sensitive(var.bot_token)
}
