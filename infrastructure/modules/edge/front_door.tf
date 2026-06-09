resource "azurerm_cdn_frontdoor_profile" "main" {
  name                = "afd-${substr(replace(var.name_prefix, "-", ""), 0, 20)}"
  resource_group_name = "rg-${var.name_prefix}"
  sku_name            = "Standard_AzureFrontDoor"
  tags                = var.common_tags
}

resource "azurerm_cdn_frontdoor_endpoint" "main" {
  name                     = "fde-${substr(replace(var.name_prefix, "-", ""), 0, 15)}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id
  tags                     = var.common_tags
}

# ─── FRONTEND (SWA) ORIGIN ────────────────────────────
resource "azurerm_cdn_frontdoor_origin_group" "frontend" {
  name                     = "og-frontend"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }

  health_probe {
    path                = "/"
    request_type        = "HEAD"
    protocol            = "Https"
    interval_in_seconds = 100
  }
}

resource "azurerm_cdn_frontdoor_origin" "frontend" {
  name                           = "origin-swa"
  cdn_frontdoor_origin_group_id  = azurerm_cdn_frontdoor_origin_group.frontend.id
  enabled                        = true
  host_name                      = azurerm_static_web_app.main.default_host_name
  http_port                      = 80
  https_port                     = 443
  origin_host_header             = azurerm_static_web_app.main.default_host_name
  priority                       = 1
  weight                         = 1000
  certificate_name_check_enabled = true
}

# ─── BACKEND (APP GATEWAY) ORIGIN ─────────────────────
resource "azurerm_cdn_frontdoor_origin_group" "backend" {
  name                     = "og-backend"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }

  health_probe {
    path                = "/health"
    request_type        = "GET"
    protocol            = "Http"
    interval_in_seconds = 30
  }
}

resource "azurerm_cdn_frontdoor_origin" "backend" {
  name                           = "origin-appgw"
  cdn_frontdoor_origin_group_id  = azurerm_cdn_frontdoor_origin_group.backend.id
  enabled                        = true
  host_name                      = azurerm_public_ip.appgw.ip_address
  http_port                      = 80
  https_port                     = 443
  origin_host_header             = azurerm_public_ip.appgw.ip_address
  priority                       = 1
  weight                         = 1000
  certificate_name_check_enabled = false
}

# ─── ROUTES ───────────────────────────────────────────
resource "azurerm_cdn_frontdoor_route" "frontend" {
  name                          = "route-frontend"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.main.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.frontend.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.frontend.id]
  enabled                       = true

  patterns_to_match      = ["/*"]
  supported_protocols    = ["Http", "Https"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = true
}

resource "azurerm_cdn_frontdoor_route" "backend" {
  name                          = "route-backend"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.main.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.backend.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.backend.id]
  enabled                       = true

  patterns_to_match      = ["/auth/*", "/emails/*", "/meetings/*", "/ai/*"]
  supported_protocols    = ["Http", "Https"]
  forwarding_protocol    = "MatchRequest"
  link_to_default_domain = true
}
