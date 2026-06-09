resource "azurerm_container_app" "meeting_service" {
  name                         = "meeting-service"
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
    target_port      = var.container_apps["meeting-service"].target_port
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    container {
      name   = "meeting-service"
      image  = "${var.acr_login_server}/aeroinbox-meeting:v1"
      cpu    = var.container_apps["meeting-service"].cpu
      memory = var.container_apps["meeting-service"].memory

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
      env {
        name  = "AI_SERVICE_URL"
        value = "http://ai-service"
      }
    }

    min_replicas = var.container_apps["meeting-service"].min_replicas
    max_replicas = var.container_apps["meeting-service"].max_replicas
  }

  tags = var.common_tags
}
