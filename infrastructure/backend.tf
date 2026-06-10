terraform {
  # Backend configuration holds the state storage setup.
  # When ready to migrate from local state to Azure Storage:
  # 1. Spin up state storage using the bootstrap template or manual container creation.
  # 2. Uncomment the block below.
  # 3. Run: terraform init -backend-config=environments/{env}/backend.tfvars

  backend "azurerm" {
    use_azuread_auth = true
  }
}
