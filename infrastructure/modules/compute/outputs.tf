output "container_app_env_id" {
  description = "The ID of the Container Apps Environment"
  value       = azurerm_container_app_environment.main.id
}

output "container_app_env_default_domain" {
  description = "Default domain of the Container Apps environment"
  value       = azurerm_container_app_environment.main.default_domain
}

output "api_service_fqdn" {
  description = "FQDN of the api-service gateway container"
  value       = azurerm_container_app.apps["api-service"].fqdn
}
