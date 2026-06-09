project_name   = "aeroinbox"
environment    = "prod"
location       = "centralindia"
location_short = "cin"

vnet_address_space = ["10.0.0.0/16"]

subnets = {
  "appgw" = {
    address_prefixes = ["10.0.1.0/24"]
  }
  "containerapps" = {
    address_prefixes   = ["10.0.2.0/23"]
    delegation_name    = "Microsoft.App.environments"
    delegation_service = "Microsoft.App/environments"
  }
  "integration" = {
    address_prefixes   = ["10.0.3.0/24"]
    delegation_name    = "Microsoft.DBforPostgreSQL.flexibleServers"
    delegation_service = "Microsoft.DBforPostgreSQL/flexibleServers"
  }
  "functions" = {
    address_prefixes = ["10.0.4.0/24"]
  }
  "privateendpoints" = {
    address_prefixes                          = ["10.0.5.0/24"]
    private_endpoint_network_policies_enabled = false
  }
}

postgres_sku_name   = "B_Standard_B2ms"
postgres_storage_mb = 65536
postgres_databases  = ["aeroinbox_main", "meetings", "rules"]
redis_capacity      = 1
redis_sku_name      = "Standard"

container_apps = {
  "api-service" = {
    cpu              = 1.0
    memory           = "2.0Gi"
    min_replicas     = 2
    max_replicas     = 10
    target_port      = 8000
    ingress_external = false
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

alert_email        = "devops@aeroinbox.com"
log_retention_days = 30

extra_tags = {
  CostCenter = "Engineering-Prod"
  Compliance = "Internal"
}
