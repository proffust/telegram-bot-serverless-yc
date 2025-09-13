//публичный доступ к функции
resource "yandex_function_iam_binding" "function-iam" {
  function_id = yandex_function.ai-bot-function.id
  role        = "serverless.functions.invoker"
  members = [
    "system:allUsers",
  ]
}

//отдельный сервис аккаунт для функции
resource "yandex_iam_service_account" "function-sa" {
  name        = "function-sa"
  description = "Service account for Yandex Function"
}

//чтение и запись в бакет с историей диалогов
resource "yandex_storage_bucket_iam_binding" "bucket-iam" {
  bucket = yandex_storage_bucket.conversation_bucket.bucket
  role      = "storage.editor"

  members = [
    "serviceAccount:${yandex_iam_service_account.function-sa.id}",
  ]
}

//доступ к foundation models
resource "yandex_resourcemanager_folder_iam_member" "models-user" {
  folder_id = var.folder_id
  role      = "ai.models.user"
  member    = "serviceAccount:${yandex_iam_service_account.function-sa.id}"
}

//доступ к генерации изображений
resource "yandex_resourcemanager_folder_iam_member" "imageGeneration-user" {
  folder_id = var.folder_id
  role      = "ai.imageGeneration.user"
  member    = "serviceAccount:${yandex_iam_service_account.function-sa.id}"
}

//доступ к транскрибации голоса в текст
resource "yandex_resourcemanager_folder_iam_member" "speechkit-stt-user" {
  folder_id = var.folder_id
  role      = "ai.speechkit-stt.user"
  member    = "serviceAccount:${yandex_iam_service_account.function-sa.id}"
}

//доступ к синтезу речи из текста
resource "yandex_resourcemanager_folder_iam_member" "speechkit-tts-user" {
  folder_id = var.folder_id
  role      = "ai.speechkit-tts.user"
  member    = "serviceAccount:${yandex_iam_service_account.function-sa.id}"
}

resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = yandex_iam_service_account.function-sa.id
  description        = "static access key for object storage"
}

resource "yandex_iam_service_account_api_key" "sa-api-key" {
  service_account_id = yandex_iam_service_account.function-sa.id
  description        = "api key for openai and yandex cloud ml sdk"
  scopes             = ["yc.ai.foundationModels.execute", "yc.ai.imageGeneration.execute"]
}