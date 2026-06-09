resource "azurerm_public_ip" "appgw" {
  name                = "pip-${local.name_prefix}-appgw"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = local.common_tags
}
