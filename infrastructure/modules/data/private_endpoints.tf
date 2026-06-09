resource "azurerm_private_endpoint" "redis" {
  name                = "pe-${azurerm_redis_cache.main.name}"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.common_tags

  private_service_connection {
    name                           = "psc-${azurerm_redis_cache.main.name}"
    private_connection_resource_id = azurerm_redis_cache.main.id
    is_manual_connection           = false
    subresource_names              = ["redisCache"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.private_dns_zone_ids["privatelink.redis.cache.windows.net"]]
  }
}

resource "azurerm_private_endpoint" "storage_blob" {
  name                = "pe-${azurerm_storage_account.main.name}-blob"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.common_tags

  private_service_connection {
    name                           = "psc-${azurerm_storage_account.main.name}-blob"
    private_connection_resource_id = azurerm_storage_account.main.id
    is_manual_connection           = false
    subresource_names              = ["blob"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.private_dns_zone_ids["privatelink.blob.core.windows.net"]]
  }
}

resource "azurerm_private_endpoint" "acr" {
  name                = "pe-${azurerm_container_registry.main.name}"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.common_tags

  private_service_connection {
    name                           = "psc-${azurerm_container_registry.main.name}"
    private_connection_resource_id = azurerm_container_registry.main.id
    is_manual_connection           = false
    subresource_names              = ["registry"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.private_dns_zone_ids["privatelink.azurecr.io"]]
  }
}
