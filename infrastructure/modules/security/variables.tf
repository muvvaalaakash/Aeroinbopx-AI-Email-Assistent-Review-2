variable "name_prefix" {
  description = "Name prefix for resource naming"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "common_tags" {
  description = "Tags applied to all security resources"
  type        = map(string)
}

variable "tenant_id" {
  description = "Azure AD Tenant ID"
  type        = string
}

variable "subnet_id" {
  description = "Private endpoints Subnet ID"
  type        = string
}

variable "private_dns_zone_id" {
  description = "Resource ID of the Private DNS Zone for Key Vault"
  type        = string
}

variable "identity_principal_id" {
  description = "Principal ID of the user-assigned managed identity"
  type        = string
}
