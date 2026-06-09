resource "azurerm_user_assigned_identity" "main" {
  name                = "id-${var.name_prefix}"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  tags                = var.common_tags
}
