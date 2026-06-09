output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "acr_login_server" {
  description = "ACR login server for docker push"
  value       = module.data.acr_login_server
}

output "static_web_app_hostname" {
  description = "Static Web App default hostname"
  value       = module.edge.static_web_app_default_hostname
}

output "static_web_app_api_key" {
  description = "SWA deployment token"
  value       = module.edge.static_web_app_api_key
  sensitive   = true
}

output "front_door_endpoint" {
  description = "Front Door endpoint URL"
  value       = module.edge.front_door_endpoint_hostname
}

output "app_gateway_public_ip" {
  description = "Application Gateway public IP"
  value       = module.edge.appgw_public_ip
}

output "key_vault_name" {
  description = "Key Vault name (for manual secret management)"
  value       = module.security.key_vault_name
}

output "key_vault_uri" {
  description = "Key Vault URI"
  value       = module.security.key_vault_uri
}

output "container_apps_env_domain" {
  description = "Container Apps default domain"
  value       = module.compute.container_app_env_default_domain
}

output "postgres_server_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = module.data.postgres_server_fqdn
  sensitive   = true
}

output "postgres_admin_password" {
  description = "PostgreSQL admin password (from Key Vault)"
  value       = module.security.postgres_password
  sensitive   = true
}
