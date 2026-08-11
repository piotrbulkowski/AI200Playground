output "storage_account_blob_endpoint" {
  description = "Paste into .env as AZURE_STORAGE_ACCOUNT_URL if it differs from the default."
  value       = azurerm_storage_account.this.primary_blob_endpoint
}

output "documents_container_name" {
  value = azurerm_storage_container.documents.name
}

output "documents_test_container_name" {
  value = azurerm_storage_container.documents_test.name
}
