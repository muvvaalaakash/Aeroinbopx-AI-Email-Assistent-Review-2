resource "azurerm_container_app_environment" "main" {
  name                           = "cae-${var.name_prefix}"
  location                       = var.location
  resource_group_name            = "rg-${var.name_prefix}"
  log_analytics_workspace_id     = var.log_analytics_workspace_id
  infrastructure_subnet_id       = var.containerapps_subnet_id
  internal_load_balancer_enabled = true

  tags = var.common_tags
}
