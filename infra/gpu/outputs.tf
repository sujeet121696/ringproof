output "public_ip" {
  value = split("/", nebius_compute_v1_instance.asr.status.network_interfaces[0].public_ip_address.address)[0]
}

output "ssh" {
  value = "ssh ${var.username}@${split("/", nebius_compute_v1_instance.asr.status.network_interfaces[0].public_ip_address.address)[0]}"
}

output "tunnel" {
  description = "Run on the PC, then set ASR_URL=http://127.0.0.1:9000 in .env."
  value       = "ssh -N -L 9000:127.0.0.1:9000 ${var.username}@${split("/", nebius_compute_v1_instance.asr.status.network_interfaces[0].public_ip_address.address)[0]}"
}
