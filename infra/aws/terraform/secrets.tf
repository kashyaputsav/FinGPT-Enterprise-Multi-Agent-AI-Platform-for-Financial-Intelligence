resource "aws_secretsmanager_secret" "jwt_secret" {
  name = "${var.project_name}/jwt-secret-key"
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret_key
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.project_name}/db-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name = "${var.project_name}/openai-api-key"
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}
