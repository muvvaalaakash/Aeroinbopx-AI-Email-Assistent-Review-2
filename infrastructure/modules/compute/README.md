# Compute Infrastructure Module

This module provisions the Container Apps Environment (`cae-aeroinbox-{env}`) injected into the virtual network, and hosts the 5 backend containerized microservices.

## Resources Created
- **Container Apps Environment**: Injected in `snet-containerapps` with internal endpoint routing.
- **Container Apps**:
  - `api-service` (VNet public gateway/orchestrator)
  - `gmail-service` (Internal only)
  - `ai-service` (Internal only)
  - `rule-engine` (Internal only)
  - `meeting-service` (Internal only)

## Inputs
- `name_prefix` (string): Workspace name prefix.
- `location` (string): Target Azure region.
- `common_tags` (map): Common tags.
- `containerapps_subnet_id` (string): Container apps subnet ID.
- `identity_id` (string): Managed identity ID.
- `identity_client_id` (string): Managed identity client ID.
- `postgres_fqdn` (string): database FQDN.
- `redis_hostname` (string): Redis cache hostname.
- `acr_login_server` (string): Registry server URL.
- `key_vault_uri` (string): Vault URI.
- `log_analytics_workspace_id` (string): Workspace logging target.
- `container_apps` (map): CPU, memory, and scaling rules for each container.

## Outputs
- `container_app_env_id` (string)
- `container_app_env_default_domain` (string)
- `api_service_fqdn` (string)
