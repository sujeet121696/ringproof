terraform {
  required_version = ">= 1.6"
  required_providers {
    nebius = {
      source  = "nebius/nebius"
      version = ">= 0.6.8"
    }
  }
}

# Signs in with NEBIUS_IAM_TOKEN when it is set (a 12-hour user token from
# `nebius iam get-access-token`, e.g. in Cloud Shell; the provider prefers it), otherwise as a
# service account with a key kept outside the repo (see README.md).
provider "nebius" {
  service_account = var.service_account_id == "" ? null : {
    account_id       = var.service_account_id
    public_key_id    = var.public_key_id
    private_key_file = pathexpand(var.private_key_file)
  }
}
