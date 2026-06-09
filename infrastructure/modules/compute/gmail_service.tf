resource "azurerm_container_app" "gmail_service" {
  name                         = "gmail-service"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = "rg-${var.name_prefix}"
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [var.identity_id]
  }

  registry {
    server   = var.acr_login_server
    identity = var.identity_id
  }

  ingress {
    external_enabled = true
    target_port      = var.container_apps["gmail-service"].target_port
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    container {
      name   = "gmail-service"
      image  = "${var.acr_login_server}/aeroinbox-gmail:v1"
      cpu    = var.container_apps["gmail-service"].cpu
      memory = var.container_apps["gmail-service"].memory

      env {
        name  = "AZURE_KEY_VAULT_URI"
        value = var.key_vault_uri
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = var.identity_client_id
      }
      env {
        name  = "DATABASE_HOST"
        value = var.postgres_fqdn
      }
    }

    min_replicas = var.container_apps["gmail-service"].min_replicas
    max_replicas = var.container_apps["gmail-service"].max_replicas
  }

  tags = var.common_tags
}
