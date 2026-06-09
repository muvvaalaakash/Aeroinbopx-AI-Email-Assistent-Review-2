# Data Infrastructure Module

This module provisions the data storage, caching, database, and container repository resources for AeroInbox, linked securely inside the private virtual network.

## Resources Created
- **PostgreSQL Flexible Server**: integrated natively inside the delegated subnet (`snet-integration`) and with Entra AD integration.
- **PostgreSQL Databases**: `aeroinbox_main`, `meetings`, `rules`.
- **Redis Cache**: standard/basic cache tier.
- **Storage Account**: blob and file storage for persistent caching.
- **Azure Container Registry**: Premium SKU hosting Docker images.
- **Private Endpoints**: for Redis Cache, Storage Account (blob), and Azure Container Registry.
- **Role Assignments**:
  - `Storage Blob Data Contributor` for managed identity.
  - `AcrPull` for managed identity.

## Inputs
- `name_prefix` (string): Workspace name prefix.
- `location` (string): Target Azure region.
- `common_tags` (map): Common tags.
- `tenant_id` (string): Azure AD tenant ID.
- `private_endpoint_subnet_id` (string): Private endpoints subnet ID.
- `postgres_subnet_id` (string): PostgreSQL delegated subnet ID.
- `identity_principal_id` (string): Managed identity principal ID.
- `key_vault_id` (string): Vault ID.
- `postgres_sku_name` (string): DB SKU.
- `postgres_storage_mb` (number): DB storage.
- `postgres_databases` (list): Database names.
- `redis_capacity` (number): Redis capacity.
- `redis_sku_name` (string): Redis SKU.
- `private_dns_zone_ids` (map): Linked Private DNS zone IDs.

## Outputs
- `postgres_server_fqdn` (string)
- `redis_hostname` (string)
- `redis_primary_connection_string` (string, sensitive)
- `acr_login_server` (string)
- `storage_account_name` (string)
- `storage_account_primary_blob_endpoint` (string)
