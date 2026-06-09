resource "azurerm_redis_cache" "main" {
  name                = "redis-${substr(replace(var.name_prefix, "-", ""), 0, 20)}"
  location            = var.location
  resource_group_name = "rg-${var.name_prefix}"
  capacity            = var.redis_capacity
  family              = var.redis_sku_name == "Premium" ? "P" : "C"
  sku_name            = var.redis_sku_name
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    # Basic / Standard configs
    maxmemory_reserved = 2
    maxmemory_delta    = 2
    maxmemory_policy   = "allkeys-lru"
  }

  tags = var.common_tags
}
