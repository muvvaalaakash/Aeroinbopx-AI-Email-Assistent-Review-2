resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.common_tags
}

module "network" {
  source = "./modules/network"

  name_prefix        = local.name_prefix
  location           = var.location
  common_tags        = local.common_tags
  vnet_address_space = var.vnet_address_space
  subnets            = var.subnets
  private_dns_zones  = local.private_dns_zones

  depends_on = [azurerm_resource_group.main]
}

module "identity" {
  source = "./modules/identity"

  name_prefix = local.name_prefix
  location    = var.location
  common_tags = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

module "security" {
  source = "./modules/security"

  name_prefix           = local.name_prefix
  location              = var.location
  common_tags           = local.common_tags
  tenant_id             = var.tenant_id
  subnet_id             = module.network.privateendpoints_subnet_id
  private_dns_zone_id   = module.network.private_dns_zone_ids["privatelink.vaultcore.azure.net"]
  identity_principal_id = module.identity.identity_principal_id

  depends_on = [module.network, module.identity]
}

module "monitoring" {
  source = "./modules/monitoring"

  name_prefix        = local.name_prefix
  location           = var.location
  common_tags        = local.common_tags
  alert_email        = var.alert_email
  log_retention_days = var.log_retention_days

  depends_on = [azurerm_resource_group.main]
}

module "data" {
  source = "./modules/data"

  name_prefix                = local.name_prefix
  location                   = var.location
  common_tags                = local.common_tags
  tenant_id                  = var.tenant_id
  private_endpoint_subnet_id = module.network.privateendpoints_subnet_id
  postgres_subnet_id         = module.network.integration_subnet_id
  identity_principal_id      = module.identity.identity_principal_id
  key_vault_id               = module.security.key_vault_id
  postgres_sku_name          = var.postgres_sku_name
  postgres_storage_mb        = var.postgres_storage_mb
  postgres_databases         = var.postgres_databases
  redis_capacity             = var.redis_capacity
  redis_sku_name             = var.redis_sku_name
  private_dns_zone_ids       = module.network.private_dns_zone_ids

  depends_on = [module.network, module.identity, module.security]
}

module "compute" {
  source = "./modules/compute"

  name_prefix                = local.name_prefix
  location                   = var.location
  common_tags                = local.common_tags
  containerapps_subnet_id    = module.network.containerapps_subnet_id
  identity_id                = module.identity.identity_id
  identity_client_id         = module.identity.identity_client_id
  postgres_fqdn              = module.data.postgres_server_fqdn
  redis_hostname             = module.data.redis_hostname
  acr_login_server           = module.data.acr_login_server
  key_vault_uri              = module.security.key_vault_uri
  log_analytics_workspace_id = module.monitoring.workspace_id
  container_apps             = var.container_apps

  depends_on = [module.data, module.monitoring]
}

module "edge" {
  source = "./modules/edge"

  name_prefix      = local.name_prefix
  location         = var.location
  common_tags      = local.common_tags
  appgw_subnet_id  = module.network.appgw_subnet_id
  api_service_fqdn = module.compute.api_service_fqdn

  depends_on = [module.compute]
}
