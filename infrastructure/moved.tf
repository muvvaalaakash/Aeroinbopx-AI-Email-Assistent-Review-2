moved {
  from = module.edge.azurerm_public_ip.appgw
  to   = azurerm_public_ip.appgw
}

moved {
  from = module.edge.azurerm_static_site.main
  to   = azurerm_static_site.main
}
