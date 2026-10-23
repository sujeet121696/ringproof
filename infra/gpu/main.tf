# One GPU VM for the speech service (asr/). Everything here is created and deleted together:
# `terraform destroy` removes the VM, its boot disk, its public IP and the firewall.

data "nebius_vpc_v1_subnet" "this" {
  id = var.subnet_id
}

# Firewall: SSH from your IP only, nothing else in. The speech service listens on 127.0.0.1 and
# is reached through an SSH tunnel (asr/README.md), so no other port is opened.
resource "nebius_vpc_v1_security_group" "asr" {
  parent_id  = var.project_id
  network_id = data.nebius_vpc_v1_subnet.this.network_id
  name       = "ringproof-asr"
}

resource "nebius_vpc_v1_security_rule" "ssh_in" {
  parent_id = nebius_vpc_v1_security_group.asr.id
  name      = "ssh-from-owner"
  access    = "ALLOW"
  protocol  = "TCP"
  ingress = {
    source_cidrs      = [var.ssh_cidr]
    destination_ports = [22]
  }
}

# Out: packages, pip, model downloads from Hugging Face.
resource "nebius_vpc_v1_security_rule" "all_out" {
  parent_id = nebius_vpc_v1_security_group.asr.id
  name      = "all-out"
  access    = "ALLOW"
  protocol  = "ANY"
  egress = {
    destination_cidrs = ["0.0.0.0/0"]
  }
}

resource "nebius_compute_v1_instance" "asr" {
  parent_id = var.project_id
  name      = "ringproof-asr"

  resources = {
    platform = var.platform
    preset   = var.preset
  }

  boot_disk = {
    attach_mode = "READ_WRITE"
    managed_disk = { # deleted with the VM
      name = "ringproof-asr-boot"
      spec = {
        type           = "NETWORK_SSD"
        size_gibibytes = var.disk_gib
        source_image_family = {
          image_family = var.image_family
        }
      }
    }
  }

  network_interfaces = [{
    name              = "eth0"
    subnet_id         = var.subnet_id
    ip_address        = {}
    public_ip_address = {}
    security_groups   = [{ id = nebius_vpc_v1_security_group.asr.id }]
  }]

  cloud_init_user_data = templatefile("${path.module}/cloud-init.yaml.tftpl", {
    username       = var.username
    ssh_public_key = trimspace(file(pathexpand(var.ssh_public_key_file)))
  })

  depends_on = [nebius_vpc_v1_security_rule.ssh_in, nebius_vpc_v1_security_rule.all_out]
}
