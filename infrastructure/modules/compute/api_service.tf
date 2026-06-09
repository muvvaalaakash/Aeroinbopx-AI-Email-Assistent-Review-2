resource "azurerm_container_app" "api_service" {
  name                         = "api-service"
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
    target_port      = var.container_apps["api-service"].target_port
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    container {
      name   = "api-service"
      image  = "${var.acr_login_server}/aeroinbox-api:v1"
      cpu    = var.container_apps["api-service"].cpu
      memory = var.container_apps["api-service"].memory

      env {
        name  = "AZURE_KEY_VAULT_URI"
        value = var.key_vault_uri
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = var.identity_client_id
      }
      env {
        name  = "REDIS_HOST"
        value = var.redis_hostname
      }
      env {
        name  = "REDIS_PORT"
        value = "6379"
      }
      env {
        name  = "REDIS_SSL"
        value = "False"
      }
      env {
        name  = "REDIS_PASSWORD"
        value = ""
      }
      env {
        name  = "DATABASE_HOST"
        value = var.postgres_fqdn
      }
      env {
        name  = "GMAIL_SERVICE_URL"
        value = "http://gmail-service"
      }
      env {
        name  = "AI_SERVICE_URL"
        value = "http://ai-service"
      }
      env {
        name  = "RULE_ENGINE_SERVICE_URL"
        value = "http://rule-engine"
      }
      env {
        name  = "MEETING_SERVICE_URL"
        value = "http://meeting-service"
      }
    }

    min_replicas = var.container_apps["api-service"].min_replicas
    max_replicas = var.container_apps["api-service"].max_replicas
  }

  tags = var.common_tags
}
