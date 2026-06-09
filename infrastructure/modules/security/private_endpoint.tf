resource "azurerm_private_endpoint" "kv" {
  name                = "pe-${azurerm_key_vault.main.name}"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  subnet_id           = var.subnet_id
  tags                = var.common_tags

  private_service_connection {
    name                           = "psc-${azurerm_key_vault.main.name}"
    private_connection_resource_id = azurerm_key_vault.main.id
    is_manual_connection             = false
    subresource_names              = ["vault"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.private_dns_zone_id]
  }
}
