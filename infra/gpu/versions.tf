terraform {
  required_version = ">= 1.6"
  required_providers {
    nebius = {
      source  = "nebius/nebius"
      version = ">= 0.6.8"
    }
  }
}

# Signs in as a service account with a key kept outside the repo (see README.md).
provider "nebius" {
  service_account = {
    account_id       = var.service_account_id
    public_key_id    = var.public_key_id
    private_key_file = pathexpand(var.private_key_file)
  }
}
