# Makefile for common Terraform commands

.PHONY: help init plan apply destroy fmt validate clean output

ENV ?= prod  # Default environment

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init: ## Initialize terraform with backend
	terraform init -backend-config=environments/$(ENV)/backend.tfvars -reconfigure

plan: ## Show terraform plan
	terraform plan -var-file=environments/$(ENV)/terraform.tfvars -out=tfplan

apply: ## Apply terraform changes
	terraform apply -var-file=environments/$(ENV)/terraform.tfvars -auto-approve

destroy: ## Destroy all resources (DANGEROUS!)
	terraform destroy -var-file=environments/$(ENV)/terraform.tfvars

fmt: ## Format terraform files
	terraform fmt -recursive

validate: ## Validate terraform configuration
	terraform validate

clean: ## Clean terraform cache
	rm -rf .terraform/
	rm -f tfplan
	rm -f *.tfstate*

output: ## Show terraform outputs
	terraform output
