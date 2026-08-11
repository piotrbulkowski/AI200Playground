# Phase 1: Blob Storage for document uploads. AAD-only auth — shared_access_key_enabled = false
# means no account key can ever be used, forcing DefaultAzureCredential end to end.
resource "azurerm_storage_account" "this" {
  name                = var.storage_account_name
  resource_group_name = data.azurerm_resource_group.this.name
  location            = data.azurerm_resource_group.this.location

  account_tier              = "Standard"
  account_replication_type  = "LRS"
  min_tls_version           = "TLS1_2"
  shared_access_key_enabled = false
}

resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

# Isolated container for integration tests (Phase 1's `test` config profile) so tests never
# touch the same blobs as day-to-day development.
resource "azurerm_storage_container" "documents_test" {
  name                  = "documents-test"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}
