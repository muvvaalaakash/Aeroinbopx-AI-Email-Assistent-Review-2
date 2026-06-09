locals {
  effective_environment = (
    terraform.workspace != "default" 
    ? terraform.workspace 
    : var.environment
  )

  name_prefix = "${var.project_name}-${local.effective_environment}"

  common_tags = merge({
    Environment = local.effective_environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Workspace   = terraform.workspace
    Owner       = "DevOps"
    CostCenter  = "Engineering"
    Application = "AeroInbox-Email-Assistant"
  }, var.extra_tags)

  private_dns_zones = [
    "privatelink.vaultcore.azure.net",
    "privatelink.postgres.database.azure.com",
    "privatelink.blob.core.windows.net",
    "privatelink.file.core.windows.net",
    "privatelink.azurecr.io",
    "privatelink.redis.cache.windows.net"
  ]
}
