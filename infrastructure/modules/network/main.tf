resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.name_prefix}"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  address_space       = var.vnet_address_space
  tags                = var.common_tags
}

resource "azurerm_subnet" "subnets" {
  for_each             = var.subnets
  name                 = "snet-${each.key}"
  resource_group_name  = "rg-${var.name_prefix}"
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = each.value.address_prefixes
  service_endpoints    = each.value.service_endpoints

  private_endpoint_network_policies_enabled = each.value.private_endpoint_network_policies_enabled

  dynamic "delegation" {
    for_each = each.value.delegation_name != null ? [1] : []
    content {
      name = each.value.delegation_name
      service_delegation {
        name    = each.value.delegation_service
        actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
      }
    }
  }
}
