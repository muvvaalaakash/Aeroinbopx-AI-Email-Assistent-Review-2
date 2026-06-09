output "vnet_id" {
  description = "The ID of the Virtual Network"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "The name of the Virtual Network"
  value       = azurerm_virtual_network.main.name
}

output "appgw_subnet_id" {
  description = "The ID of the Application Gateway subnet"
  value       = azurerm_subnet.subnets["appgw"].id
}

output "containerapps_subnet_id" {
  description = "The ID of the Container Apps subnet"
  value       = azurerm_subnet.subnets["containerapps"].id
}

output "integration_subnet_id" {
  description = "The ID of the PostgreSQL Integration subnet"
  value       = azurerm_subnet.subnets["integration"].id
}

output "privateendpoints_subnet_id" {
  description = "The ID of the Private Endpoints subnet"
  value       = azurerm_subnet.subnets["privateendpoints"].id
}

output "private_dns_zone_ids" {
  description = "Map of Private DNS Zone names to their resource IDs"
  value       = { for zone in var.private_dns_zones : zone => azurerm_private_dns_zone.dns_zones[zone].id }
}
