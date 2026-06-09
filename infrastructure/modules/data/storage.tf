resource "azurerm_storage_account" "main" {
  name                            = "st${substr(replace(var.name_prefix, "-", ""), 0, 20)}"
  resource_group_name             = "rg-${var.name_prefix}"
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = var.common_tags
}

resource "azurerm_storage_container" "media" {
  name                  = "media"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_role_assignment" "storage_identity" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.identity_principal_id
}
