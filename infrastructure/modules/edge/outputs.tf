output "static_web_app_default_hostname" {
  description = "Default hostname of the Static Web App"
  value       = azurerm_static_site.main.default_host_name
}

output "static_web_app_api_key" {
  description = "API Key/token used to deploy Static Web App"
  value       = azurerm_static_site.main.api_key
  sensitive   = true
}

output "front_door_endpoint_hostname" {
  description = "Hostname of the Azure Front Door endpoint"
  value       = azurerm_cdn_frontdoor_endpoint.main.host_name
}

output "appgw_public_ip" {
  description = "Public IP of the Application Gateway"
  value       = azurerm_public_ip.appgw.ip_address
}
