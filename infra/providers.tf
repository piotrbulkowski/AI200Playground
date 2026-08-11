terraform {
  required_version = ">= 1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}

  # Required when shared_access_key_enabled = false — otherwise the provider's own
  # post-create "wait for data plane availability" check tries key-based auth and fails
  # with a 403 KeyBasedAuthenticationNotPermitted, even though the resource was created fine.
  storage_use_azuread = true
}
