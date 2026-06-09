# Identity Infrastructure Module

This module provisions the User-Assigned Managed Identity that is injected into Container Apps to enable passwordless resource access via Microsoft Entra ID.

## Resources Created
- **User-Assigned Managed Identity**: `id-aeroinbox-{env}`

## Inputs
- `name_prefix` (string): Workspace name prefix.
- `location` (string): Target Azure region.
- `common_tags` (map): Common tags.

## Outputs
- `identity_id` (string): Full Resource ID.
- `identity_client_id` (string): Client ID of the identity.
- `identity_principal_id` (string): Object/Principal ID for RBAC.
