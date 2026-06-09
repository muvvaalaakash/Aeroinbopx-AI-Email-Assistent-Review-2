resource "random_password" "postgres" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
  min_upper        = 4
  min_lower        = 4
  min_numeric      = 4
  min_special      = 2
}

resource "random_password" "session" {
  length  = 64
  special = false
}

resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-admin-password"
  value        = random_password.postgres.result
  key_vault_id = azurerm_key_vault.main.id
  content_type = "password"

  depends_on = [azurerm_role_assignment.admin]
}

resource "azurerm_key_vault_secret" "session_secret" {
  name         = "session-secret"
  value        = random_password.session.result
  key_vault_id = azurerm_key_vault.main.id
  content_type = "password"

  depends_on = [azurerm_role_assignment.admin]
}

resource "azurerm_key_vault_secret" "google_client_id" {
  name         = "google-client-id"
  value        = "PLACEHOLDER_UPDATE_AFTER_DEPLOY"
  key_vault_id = azurerm_key_vault.main.id
  content_type = "oauth-credential"

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_role_assignment.admin]
}

resource "azurerm_key_vault_secret" "google_client_secret" {
  name         = "google-client-secret"
  value        = "PLACEHOLDER_UPDATE_AFTER_DEPLOY"
  key_vault_id = azurerm_key_vault.main.id
  content_type = "oauth-credential"

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_role_assignment.admin]
}

resource "azurerm_key_vault_secret" "ai_provider_key" {
  name         = "gemini-api-key"
  value        = "PLACEHOLDER_UPDATE_AFTER_DEPLOY"
  key_vault_id = azurerm_key_vault.main.id
  content_type = "api-key"

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_role_assignment.admin]
}
