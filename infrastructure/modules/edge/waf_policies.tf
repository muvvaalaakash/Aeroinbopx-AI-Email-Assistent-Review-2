resource "azurerm_web_application_firewall_policy" "appgw" {
  name                = "waf-${var.name_prefix}-appgw"
  resource_group_name = "rg-${var.name_prefix}"
  location            = var.location
  tags                = var.common_tags

  policy_settings {
    enabled                     = true
    mode                        = "Prevention"
    request_body_check          = true
    max_request_body_size_in_kb = 128
    file_upload_limit_in_mb     = 100
  }

  managed_rules {
    managed_rule_set {
      type    = "OWASP"
      version = "3.2"
    }
  }
}
