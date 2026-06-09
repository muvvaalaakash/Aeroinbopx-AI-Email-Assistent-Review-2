variable "name_prefix" {
  description = "Name prefix for resource naming"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "common_tags" {
  description = "Tags applied to all edge resources"
  type        = map(string)
}

variable "appgw_subnet_id" {
  description = "Subnet ID for Application Gateway"
  type        = string
}

variable "api_service_fqdn" {
  description = "Internal FQDN of the api-service gateway container"
  type        = string
}

variable "appgw_public_ip_id" {
  description = "Resource ID of the public IP for Application Gateway"
  type        = string
}

