variable "project_id" {
  description = "Nebius project ID (project-...), in region eu-north1, where L40S is offered."
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID (vpcsubnet-...) in that project."
  type        = string
}

variable "service_account_id" {
  description = "Service account ID (serviceaccount-...) that Terraform signs in as."
  type        = string
}

variable "public_key_id" {
  description = "ID of the authorized key uploaded for that service account (publickey-...)."
  type        = string
}

variable "private_key_file" {
  description = "Private key of that authorized key. Kept outside the repo."
  type        = string
  default     = "~/.nebius-sa/ringproof-terraform/private.pem"
}

variable "ssh_cidr" {
  description = "Only this address range may SSH in: your own public IP as x.x.x.x/32."
  type        = string
  validation {
    condition     = can(cidrnetmask(var.ssh_cidr)) && var.ssh_cidr != "0.0.0.0/0"
    error_message = "Use your own public IP as x.x.x.x/32, not the whole internet."
  }
}

variable "ssh_public_key_file" {
  description = "Public SSH key put on the VM."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "username" {
  description = "Login user on the VM (not root or admin)."
  type        = string
  default     = "sujeet"
}

# Defaults: the smallest L40S (docs.nebius.com/compute/virtual-machines/types) and the GPU image
# Nebius recommends for it (docs.nebius.com/compute/storage/boot-disk-images), checked Oct 23.
variable "platform" {
  type    = string
  default = "gpu-l40s-a"
}

variable "preset" {
  type    = string
  default = "1gpu-8vcpu-32gb"
}

variable "image_family" {
  type    = string
  default = "ubuntu24.04-cuda13.0"
}

variable "disk_gib" {
  description = "Boot disk size: the speech models and NeMo take tens of GB."
  type        = number
  default     = 100
}
