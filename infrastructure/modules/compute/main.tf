resource "azurerm_container_app_environment" "main" {
  name                           = "cae-${var.name_prefix}"
  location                       = var.location
  resource_group_name            = "rg-${var.name_prefix}"
  log_analytics_workspace_id     = var.log_analytics_workspace_id
  infrastructure_subnet_id       = var.containerapps_subnet_id
  internal_load_balancer_enabled = false

  tags = var.common_tags
}

resource "azurerm_private_dns_zone" "containerapps" {
  name                = azurerm_container_app_environment.main.default_domain
  resource_group_name = "rg-${var.name_prefix}"
  tags                = var.common_tags
}

resource "azurerm_private_dns_a_record" "containerapps_wildcard" {
  name                = "*"
  zone_name           = azurerm_private_dns_zone.containerapps.name
  resource_group_name = "rg-${var.name_prefix}"
  ttl                 = 3600
  records             = [azurerm_container_app_environment.main.static_ip_address]
}

resource "azurerm_private_dns_zone_virtual_network_link" "containerapps" {
  name                  = "link-${replace(azurerm_container_app_environment.main.default_domain, ".", "-")}"
  resource_group_name   = "rg-${var.name_prefix}"
  private_dns_zone_name = azurerm_private_dns_zone.containerapps.name
  virtual_network_id    = var.vnet_id
  tags                  = var.common_tags
}
