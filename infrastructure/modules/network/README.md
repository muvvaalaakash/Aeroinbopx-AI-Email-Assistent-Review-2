# Network Infrastructure Module

This module provisions the foundation VNet, subnets (including delegations for Container Apps and PostgreSQL), Network Security Groups (NSGs), and Private DNS zones for private endpoint integration.

## Resources Created
- **Virtual Network**: `vnet-aeroinbox-{env}`
- **Subnets**: `snet-appgw`, `snet-containerapps`, `snet-integration`, `snet-functions`, `snet-privateendpoints`
- **Network Security Groups**: `nsg-aeroinbox-{env}-appgw` (with open HTTP/S and GatewayManager ports) and `nsg-aeroinbox-{env}-default`
- **Private DNS Zones**: linked to VNet for vaultcore, postgres, blob, file, redis, and azurecr.

## Inputs
- `name_prefix` (string): Workspace name prefix.
- `location` (string): Target Azure region.
- `common_tags` (map): Common tags.
- `vnet_address_space` (list): VNet address space.
- `subnets` (map): Detailed subnet layout with delegations.
- `private_dns_zones` (list): List of private DNS zones.

## Outputs
- `vnet_id` (string)
- `vnet_name` (string)
- `appgw_subnet_id` (string)
- `containerapps_subnet_id` (string)
- `integration_subnet_id` (string)
- `privateendpoints_subnet_id` (string)
- `private_dns_zone_ids` (map)
