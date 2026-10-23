# GPU VM for the speech service (Terraform)

One Nebius L40S VM for `asr/`, created and deleted with one command each. **Billed per hour while
it exists** (from $1.55/GPU-hour for L40S on nebius.com/prices, checked Oct 23): destroy it when done.

What it creates: the VM, a 100 GiB boot disk and a public IP (both deleted with the VM), and a
firewall that lets in SSH from one IP only. The speech service is reached through an SSH tunnel.

## One-time setup

Terraform signs in as a service account, so no personal token is stored. The private key lives in
`~/.nebius-sa/ringproof-terraform/` (outside the repo, readable only by you).

1. Key pair (already made on Sujeet's PC):
   ```bash
   mkdir -p ~/.nebius-sa/ringproof-terraform && cd ~/.nebius-sa/ringproof-terraform
   openssl genrsa -out private.pem 4096 && openssl rsa -in private.pem -outform PEM -pubout -out public.pem
   ```
2. In https://console.nebius.com: **Administration → IAM → Create resource → Service account**
   (`ringproof-terraform`), then its actions menu **→ Add to group → editors**.
3. Open the service account → **Upload authorized key** → attach `public.pem` → set an expiry
   (e.g. Oct 31) → **Upload key**. Note the key ID and the service account ID.
4. Copy `terraform.tfvars.example` to `terraform.tfvars` and fill in the IDs (project and subnet
   from the console: the project in region eu-north1, and **Network → Subnets**). `ssh_cidr` is your
   public IP + `/32`; if your IP changes, update it and run `terraform apply` again.

## Use

```bash
cd infra/gpu
terraform init
terraform apply      # shows the plan; type "yes". Prints the SSH and tunnel commands
terraform destroy    # when done: removes everything this created
```

Then follow `asr/README.md` on the VM.
