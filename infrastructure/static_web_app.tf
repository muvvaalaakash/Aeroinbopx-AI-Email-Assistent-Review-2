resource "azurerm_static_site" "main" {
  name                = "swa-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = "eastasia" # SWA metadata region
  sku_tier            = "Free"
  sku_size            = "Free"

  tags = local.common_tags
}
