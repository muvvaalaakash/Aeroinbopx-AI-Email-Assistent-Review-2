resource "azurerm_private_dns_zone" "dns_zones" {
  for_each            = toset(var.private_dns_zones)
  name                = each.key
  resource_group_name = "rg-${var.name_prefix}"
  tags                = var.common_tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "links" {
  for_each              = toset(var.private_dns_zones)
  name                  = "link-${replace(each.key, ".", "-")}"
  resource_group_name   = "rg-${var.name_prefix}"
  private_dns_zone_name = azurerm_private_dns_zone.dns_zones[each.key].name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = false
  tags                  = var.common_tags
}
