resource "azurerm_monitor_action_group" "main" {
  name                = "ag-${var.name_prefix}"
  resource_group_name = "rg-${var.name_prefix}"
  short_name          = "aeroalerts"

  email_receiver {
    name                    = "DevOps"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }

  tags = var.common_tags
}
