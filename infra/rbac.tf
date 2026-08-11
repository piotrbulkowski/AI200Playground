locals {
  developer_principal_id = coalesce(var.developer_object_id, data.azurerm_client_config.current.object_id)
}

# Data-plane role — lets DefaultAzureCredential (az login) read/write blobs without any
# storage account key ever existing.
resource "azurerm_role_assignment" "developer_blob_data_contributor" {
  scope                = azurerm_storage_account.this.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = local.developer_principal_id
}
