# Fetch the generated PostgreSQL admin password from Key Vault
data "azurerm_key_vault_secret" "postgres_admin_password" {
  name         = "postgres-admin-password"
  key_vault_id = var.key_vault_id
}
