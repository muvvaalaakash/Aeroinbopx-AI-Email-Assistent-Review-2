variable "name_prefix" {
  description = "Name prefix for resource naming"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "common_tags" {
  description = "Tags applied to all monitoring resources"
  type        = map(string)
}

variable "alert_email" {
  description = "Email address to receive monitoring alerts"
  type        = string
}

variable "log_retention_days" {
  description = "Number of days to retain logs in Log Analytics"
  type        = number
}
