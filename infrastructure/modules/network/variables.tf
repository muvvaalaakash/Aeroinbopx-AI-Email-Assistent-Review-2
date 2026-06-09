variable "name_prefix" {
  description = "Name prefix for resource naming"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "common_tags" {
  description = "Tags applied to all network resources"
  type        = map(string)
}

variable "vnet_address_space" {
  description = "Address space for the Virtual Network"
  type        = list(string)
}

variable "subnets" {
  description = "Map of subnet configurations"
  type = map(object({
    address_prefixes                          = list(string)
    delegation_name                           = optional(string, null)
    delegation_service                        = optional(string, null)
    service_endpoints                         = optional(list(string), [])
    private_endpoint_network_policies_enabled = optional(bool, true)
  }))
}

variable "private_dns_zones" {
  description = "List of Private DNS zones to create and link"
  type        = list(string)
}
