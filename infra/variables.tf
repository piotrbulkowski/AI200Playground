variable "resource_group_name" {
  description = "Existing resource group to provision into. Not created by this config."
  type        = string
  default     = "rg-ai200playground"
}

variable "storage_account_name" {
  description = "Globally unique Storage Account name (3-24 lowercase alphanumeric characters)."
  type        = string
  default     = "ai200playgrounddev"
}

variable "developer_object_id" {
  description = <<-EOT
    Azure AD object ID of the developer identity to grant Storage Blob Data Contributor.
    Defaults to whoever is running `terraform apply` (via az login) when left null.
  EOT
  type        = string
  default     = null
}
