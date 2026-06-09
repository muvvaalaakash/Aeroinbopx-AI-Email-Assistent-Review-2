resource "azurerm_public_ip" "appgw" {
  name                = "pip-${var.name_prefix}-appgw"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = var.common_tags
}

locals {
  backend_address_pool_name      = "apipool"
  frontend_port_name             = "http-port"
  frontend_ip_configuration_name = "appgw-ip-config"
  http_setting_name              = "http-setting"
  listener_name                  = "http-listener"
  request_routing_rule_name      = "routing-rule"
}

resource "azurerm_application_gateway" "main" {
  name                = "appgw-${var.name_prefix}"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  tags                = var.common_tags

  sku {
    name     = "WAF_v2"
    tier     = "WAF_v2"
    capacity = 1
  }

  gateway_ip_configuration {
    name      = "gateway-ip-config"
    subnet_id = var.appgw_subnet_id
  }

  frontend_ip_configuration {
    name                 = local.frontend_ip_configuration_name
    public_ip_address_id = azurerm_public_ip.appgw.id
  }

  frontend_port {
    name = local.frontend_port_name
    port = 80
  }

  backend_address_pool {
    name  = local.backend_address_pool_name
    fqdns = [var.api_service_fqdn]
  }

  backend_http_settings {
    name                                = local.http_setting_name
    cookie_based_affinity               = "Disabled"
    port                                = 80
    protocol                            = "Http"
    request_timeout                     = 60
    pick_host_name_from_backend_address = true
  }

  http_listener {
    name                           = local.listener_name
    frontend_ip_configuration_name = local.frontend_ip_configuration_name
    frontend_port_name             = local.frontend_port_name
    protocol                       = "Http"
  }

  request_routing_rule {
    name                       = local.request_routing_rule_name
    rule_type                  = "Basic"
    http_listener_name         = local.listener_name
    backend_address_pool_name  = local.backend_address_pool_name
    backend_http_settings_name = local.http_setting_name
    priority                   = 100
  }

  firewall_policy_id = azurerm_web_application_firewall_policy.appgw.id
}
