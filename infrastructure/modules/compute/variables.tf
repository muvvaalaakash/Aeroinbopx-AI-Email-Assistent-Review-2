variable "name_prefix" {
  description = "Name prefix for resource naming"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "common_tags" {
  description = "Tags applied to all compute resources"
  type        = map(string)
}

variable "containerapps_subnet_id" {
  description = "Subnet ID delegated to Container Apps"
  type        = string
}

variable "identity_id" {
  description = "Full resource ID of the managed identity"
  type        = string
}

variable "identity_client_id" {
  description = "Client ID of the managed identity"
  type        = string
}

variable "postgres_fqdn" {
  description = "PostgreSQL flexible server FQDN"
  type        = string
}

variable "redis_hostname" {
  description = "Redis Cache hostname"
  type        = string
}

variable "acr_login_server" {
  description = "Azure Container Registry login server"
  type        = string
}

variable "key_vault_uri" {
  description = "URI of the Azure Key Vault"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics Workspace"
  type        = string
}

variable "container_apps" {
  description = "Map of container app resource scaling settings"
  type = map(object({
    cpu                 = number
    memory              = string
    min_replicas        = number
    max_replicas        = number
    target_port         = number
    concurrent_requests = optional(number, 100)
    ingress_external    = optional(bool, false)
  }))
}

variable "vnet_id" {
  description = "The ID of the Virtual Network for Private DNS Zone links"
  type        = string
}
