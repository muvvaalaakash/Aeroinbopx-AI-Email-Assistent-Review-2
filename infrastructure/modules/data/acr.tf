resource "azurerm_container_registry" "main" {
  name                = "acr${substr(replace(var.name_prefix, "-", ""), 0, 20)}"
  resource_group_name = "rg-${var.name_prefix}"
  location            = var.location
  sku                 = "Premium" # Required for Private Endpoints
  admin_enabled       = true

  tags = var.common_tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = var.identity_principal_id
}
