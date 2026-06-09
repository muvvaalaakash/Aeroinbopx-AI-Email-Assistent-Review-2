# Security Infrastructure Module

This module provisions the Azure Key Vault (`kv-aeroinbox-{env}`), handles role assignments, automatically generates secure administrative passwords, and configures a Private Endpoint for secure internal access.

## Resources Created
- **Azure Key Vault**: with RBAC authorization enabled.
- **Key Vault Secrets**:
  - `postgres-admin-password` (randomly generated)
  - `session-secret` (randomly generated)
  - `google-client-id` (placeholder, changes ignored)
  - `google-client-secret` (placeholder, changes ignored)
  - `gemini-api-key` (placeholder, changes ignored)
- **Role Assignments**:
  - `Key Vault Administrator` for the deployer.
  - `Key Vault Secrets User` for the Container Apps user managed identity.
- **Private Endpoint**: links the vault to the VNet with automatic Private DNS resolution.

## Inputs
- `name_prefix` (string): Workspace name prefix.
- `location` (string): Target Azure region.
- `common_tags` (map): Common tags.
- `tenant_id` (string): Azure AD tenant ID.
- `subnet_id` (string): Private endpoints subnet ID.
- `private_dns_zone_id` (string): Key Vault Private DNS Zone resource ID.
- `identity_principal_id` (string): Managed identity principal ID.

## Outputs
- `key_vault_id` (string)
- `key_vault_name` (string)
- `key_vault_uri` (string)
- `postgres_password` (string, sensitive)
