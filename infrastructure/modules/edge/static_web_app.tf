resource "azurerm_static_web_app" "main" {
  name                = "swa-${var.name_prefix}"
  resource_group_name = "rg-${var.name_prefix}"
  location            = "eastasia" # SWA metadata region
  sku_tier            = "Free"
  sku_size            = "Free"

  tags = var.common_tags
}
