terraform {
  # Backend configuration holds the state storage setup.
  # When ready to migrate from local state to Azure Storage:
  # 1. Spin up state storage using the bootstrap template or manual container creation.
  # 2. Uncomment the block below.
  # 3. Run: terraform init -backend-config=environments/{env}/backend.tfvars

  # backend "azurerm" {
  #   # Parameters are resolved dynamically via the backend-config tfvars files
  #   # resource_group_name  = "rg-aeroinbox-tfstate"
  #   # storage_account_name = "staeroinboxtfstate"
  #   # container_name       = "tfstate"
  #   # key                  = "prod.terraform.tfstate"
  #   # use_azuread_auth     = true
  # }
}
