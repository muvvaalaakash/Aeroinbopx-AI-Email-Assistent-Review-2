data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  # Key Vault name must be between 3 and 24 characters
  name                          = "kv-${substr(replace(var.name_prefix, "-", ""), 0, 20)}"
  location                      = var.location
  resource_group_name           = "rg-${var.name_prefix}"
  tenant_id                     = var.tenant_id
  sku_name                      = "standard"
  enable_rbac_authorization     = true
  purge_protection_enabled      = false
  soft_delete_retention_days    = 7
  public_network_access_enabled = true

  tags = var.common_tags
}

resource "azurerm_role_assignment" "admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "identity_secrets" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.identity_principal_id
}
