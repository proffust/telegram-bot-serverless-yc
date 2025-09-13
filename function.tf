resource "yandex_function" "ai-bot-function" {
  name               = "telegram-ai-bot-serverless"
  description        = "Telegram AI bot serverless function"
  runtime            = "python39"
  entrypoint         = "main.handler"
  memory             = "256"
  execution_timeout  = "60"
  user_hash          = data.archive_file.source.output_sha256
  service_account_id = yandex_iam_service_account.function-sa.id
  package {
    bucket_name = yandex_storage_bucket.code-bucket.bucket
    object_name = yandex_storage_object.function-zip.key
  }
  environment = {
    TELEGRAM_BOT_TOKEN = var.bot_token,
    OPENAI_API_KEY = yandex_iam_service_account_api_key.sa-api-key.secret_key,
    AWS_ACCESS_KEY_ID = yandex_iam_service_account_static_access_key.sa-static-key.access_key,
    AWS_SECRET_ACCESS_KEY = yandex_iam_service_account_static_access_key.sa-static-key.secret_key,
    YANDEX_CLOUD_FOLDER = var.folder_id
    CONVERSATION_BUCKET = yandex_storage_bucket.conversation_bucket.bucket
  }
  depends_on = [
    yandex_storage_object.function-zip,
    yandex_iam_service_account.function-sa,
    yandex_iam_service_account_static_access_key.sa-static-key,
    yandex_iam_service_account_api_key.sa-api-key,
    yandex_storage_bucket.conversation_bucket,
  ]
}
