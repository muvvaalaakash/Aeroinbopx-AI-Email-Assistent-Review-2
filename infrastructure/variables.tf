# ─── CORE CONFIGURATION ───────────────────────────────
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "aeroinbox"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must be lowercase alphanumeric with hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "centralindia"
}

variable "location_short" {
  description = "Short form of location for naming"
  type        = string
  default     = "cin"
}

# ─── AUTHENTICATION ───────────────────────────────────
variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Azure AD Tenant ID"
  type        = string
  sensitive   = true
}

# ─── NETWORK ──────────────────────────────────────────
variable "vnet_address_space" {
  description = "VNet address space"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnets" {
  description = "Subnet configurations"
  type = map(object({
    address_prefixes                          = list(string)
    delegation_name                           = optional(string, null)
    delegation_service                        = optional(string, null)
    service_endpoints                         = optional(list(string), [])
    private_endpoint_network_policies_enabled = optional(bool, true)
  }))
}

# ─── DATA LAYER ───────────────────────────────────────
variable "postgres_sku_name" {
  description = "PostgreSQL SKU"
  type        = string
  default     = "B_Standard_B2ms"

  validation {
    condition     = can(regex("^(B_Standard|GP_Standard|MO_Standard)", var.postgres_sku_name))
    error_message = "Must be a valid PostgreSQL Flexible Server SKU."
  }
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 65536
}

variable "postgres_databases" {
  description = "List of databases to create"
  type        = list(string)
  default     = ["aeroinbox_main", "meetings", "rules"]
}

variable "redis_capacity" {
  description = "Redis cache capacity"
  type        = number
  default     = 1
}

variable "redis_sku_name" {
  description = "Redis SKU"
  type        = string
  default     = "Standard"
}

# ─── CONTAINER APPS ───────────────────────────────────
variable "container_apps" {
  description = "Container Apps configuration"
  type = map(object({
    cpu                 = number
    memory              = string
    min_replicas        = number
    max_replicas        = number
    target_port         = number
    concurrent_requests = optional(number, 100)
    ingress_external    = optional(bool, false)
  }))
  default = {
    "api-service" = {
      cpu                 = 1.0
      memory              = "2.0Gi"
      min_replicas        = 2
      max_replicas        = 10
      target_port         = 8000
      concurrent_requests = 100
      ingress_external    = false
    }
    "gmail-service" = {
      cpu          = 0.5
      memory       = "1.0Gi"
      min_replicas = 1
      max_replicas = 5
      target_port  = 8000
    }
    "ai-service" = {
      cpu          = 1.0
      memory       = "2.0Gi"
      min_replicas = 1
      max_replicas = 10
      target_port  = 8000
    }
    "rule-engine" = {
      cpu          = 0.5
      memory       = "1.0Gi"
      min_replicas = 1
      max_replicas = 3
      target_port  = 8000
    }
    "meeting-service" = {
      cpu          = 0.5
      memory       = "1.0Gi"
      min_replicas = 1
      max_replicas = 3
      target_port  = 8000
    }
  }
}

# ─── MONITORING ───────────────────────────────────────
variable "alert_email" {
  description = "Email for monitoring alerts"
  type        = string
}

variable "log_retention_days" {
  description = "Log Analytics retention in days"
  type        = number
  default     = 30
}

# ─── TAGS ─────────────────────────────────────────────
variable "extra_tags" {
  description = "Additional tags to apply"
  type        = map(string)
  default     = {}
}
