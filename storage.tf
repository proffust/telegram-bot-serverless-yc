data "archive_file" "source" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/function.zip"
}

resource "yandex_storage_bucket" "code-bucket" {
  bucket     = "telegram-bot-code-${var.folder_id}"
  max_size   = 262144000
}

resource "yandex_storage_object" "function-zip" {
  bucket = yandex_storage_bucket.code-bucket.bucket
  key    = "function.zip"
  source = data.archive_file.source.output_path
  acl    = "private"
  source_hash = data.archive_file.source.output_sha256
}


resource "yandex_storage_bucket" "conversation_bucket" {
  bucket     = "${var.conversation_bucket_prefix}-${var.folder_id}"
  max_size   = 104857600
}
