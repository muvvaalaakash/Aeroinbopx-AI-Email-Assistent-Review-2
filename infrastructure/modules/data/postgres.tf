resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-${substr(replace(var.name_prefix, "_", "-"), 0, 20)}"
  location               = var.location
  resource_group_name    = "rg-${var.name_prefix}"
  sku_name               = var.postgres_sku_name
  version                = "15"
  administrator_login    = "pgadmin"
  administrator_password = data.azurerm_key_vault_secret.postgres_admin_password.value
  storage_mb             = var.postgres_storage_mb
  backup_retention_days  = 7

  delegated_subnet_id = var.postgres_subnet_id
  private_dns_zone_id = var.private_dns_zone_ids["privatelink.postgres.database.azure.com"]

  tags = var.common_tags
}

resource "azurerm_postgresql_flexible_server_database" "databases" {
  for_each  = toset(var.postgres_databases)
  name      = each.key
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

resource "azurerm_postgresql_flexible_server_active_directory_administrator" "entra" {
  server_id      = azurerm_postgresql_flexible_server.main.id
  tenant_id      = var.tenant_id
  object_id      = var.identity_principal_id
  principal_name = "id-${var.name_prefix}"
  principal_type = "ServicePrincipal"
}
