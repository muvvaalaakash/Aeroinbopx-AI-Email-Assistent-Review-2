# Edge routing Infrastructure Module

This module provisions global and regional ingress endpoints, routing public traffic to either static frontend sites or backend APIs with integrated WAF filters.

## Resources Created
- **Azure Static Web App**: Hosts the SWA-ready React SPA.
- **Application Gateway (WAF v2)**: Regional load balancer routing API calls. Exposes a public IP.
- **WAF Policy**: Standard OWASP 3.2 rule group.
- **Azure Front Door (Standard)**: Global CDN with proxy routes directing `/*` to SWA and `/auth/*`, `/emails/*`, etc. to the Application Gateway.

## Inputs
- `name_prefix` (string): Workspace name prefix.
- `location` (string): Target Azure region.
- `common_tags` (map): Common tags.
- `appgw_subnet_id` (string): Regional gateway subnet.
- `api_service_fqdn` (string): Internal API backend FQDN.

## Outputs
- `static_web_app_default_hostname` (string)
- `static_web_app_api_key` (string, sensitive)
- `front_door_endpoint_hostname` (string)
- `appgw_public_ip` (string)
