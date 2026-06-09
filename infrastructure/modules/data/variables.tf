variable "name_prefix" {
  description = "Name prefix for resource naming"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "common_tags" {
  description = "Tags applied to all data resources"
  type        = map(string)
}

variable "tenant_id" {
  description = "Azure AD Tenant ID"
  type        = string
}

variable "private_endpoint_subnet_id" {
  description = "Subnet ID for Private Endpoints"
  type        = string
}

variable "postgres_subnet_id" {
  description = "Subnet ID for PostgreSQL integration (delegated)"
  type        = string
}

variable "identity_principal_id" {
  description = "Principal ID of the user-assigned managed identity"
  type        = string
}

variable "key_vault_id" {
  description = "Resource ID of the Key Vault to read secrets"
  type        = string
}

variable "postgres_sku_name" {
  description = "PostgreSQL flexible server SKU name"
  type        = string
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage size in MB"
  type        = number
}

variable "postgres_databases" {
  description = "List of databases to create"
  type        = list(string)
}

variable "redis_capacity" {
  description = "Redis Cache capacity tier"
  type        = number
}

variable "redis_sku_name" {
  description = "Redis Cache SKU tier"
  type        = string
}

variable "private_dns_zone_ids" {
  description = "Map of Private DNS Zone names to their resource IDs"
  type        = map(string)
}
