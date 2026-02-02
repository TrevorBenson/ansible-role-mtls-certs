# ansible-role-mtls-certs

Generate self-signed mTLS (mutual TLS) certificate chains for secure client-server authentication.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## Overview

This Ansible role generates a complete mTLS certificate chain:

- **CA Certificate** - Self-signed root certificate authority (4096-bit RSA)
- **Server Certificate** - Signed by CA, with SAN support (2048-bit RSA)
- **Client Certificate** - Signed by CA, for client authentication (2048-bit RSA)

### Use Cases

- KMIP servers requiring mutual TLS
- gRPC services with client authentication
- Internal microservices with mTLS
- Development/testing environments needing quick PKI setup

## Requirements

- Ansible >= 2.14
- `community.crypto` collection

```bash
ansible-galaxy collection install community.crypto
```

## Role Variables

### Directory Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `mtls_cert_dir` | `/etc/pki/mtls` | Base certificate directory |
| `mtls_cert_owner` | `root` | File owner |
| `mtls_cert_group` | `root` | File group |
| `mtls_dir_mode` | `0750` | Directory permissions |
| `mtls_cert_mode` | `0644` | Certificate file permissions |
| `mtls_key_mode` | `0600` | Private key permissions |

### CA Certificate

| Variable | Default | Description |
|----------|---------|-------------|
| `mtls_ca_common_name` | `ca-root.example.com` | CA certificate CN |
| `mtls_ca_key_size` | `4096` | CA key size (bits) |
| `mtls_ca_validity_days` | `3650` | Validity period (10 years) |
| `mtls_ca_digest` | `sha256` | Signature algorithm |

### Server Certificate

| Variable | Default | Description |
|----------|---------|-------------|
| `mtls_server_common_name` | `server.example.com` | Server certificate CN |
| `mtls_server_key_size` | `2048` | Server key size |
| `mtls_server_validity_days` | `397` | Validity (<=397 days) |
| `mtls_server_san_dns` | `[]` | Additional DNS SANs |
| `mtls_server_san_ip` | `[]` | Additional IP SANs |
| `mtls_server_use_ansible_ip` | `true` | Auto-add host IP to SAN |

### Client Certificate

| Variable | Default | Description |
|----------|---------|-------------|
| `mtls_client_common_name` | `client.example.com` | Client certificate CN |
| `mtls_client_key_size` | `2048` | Client key size |
| `mtls_client_validity_days` | `365` | Validity (1 year) |

### Generation Control

| Variable | Default | Description |
|----------|---------|-------------|
| `mtls_generate_ca` | `true` | Generate CA certificate |
| `mtls_generate_server` | `true` | Generate server certificate |
| `mtls_generate_client` | `true` | Generate client certificate |
| `mtls_force_regenerate` | `false` | Force regeneration |

## Output Paths

After running the role, certificates are available via the `mtls_paths` variable:

```yaml
mtls_paths:
  ca_pem: /etc/pki/mtls/ca/ca.pem
  ca_key: /etc/pki/mtls/ca/ca.key
  server_pem: /etc/pki/mtls/server/server.pem
  server_key: /etc/pki/mtls/server/server.key
  client_pem: /etc/pki/mtls/client/client.pem
  client_key: /etc/pki/mtls/client/client.key
```

## Example Playbooks

### Basic Usage

```yaml
- hosts: servers
  roles:
    - role: ansible-role-mtls-certs
      vars:
        mtls_ca_common_name: "myorg-ca.internal"
        mtls_server_common_name: "api.myorg.internal"
        mtls_client_common_name: "client.myorg.internal"
```

### With Custom Paths and Permissions

```yaml
- hosts: servers
  roles:
    - role: ansible-role-mtls-certs
      vars:
        mtls_cert_dir: /opt/myapp/certs
        mtls_cert_group: myapp
        mtls_key_mode: "0600"
        mtls_server_san_dns:
          - api.example.com
          - api-internal.example.com
        mtls_server_san_ip:
          - 10.0.0.50
```

### Integration with KMIP Role

```yaml
- hosts: kmip_servers
  pre_tasks:
    - name: Generate mTLS certificates
      include_role:
        name: ansible-role-mtls-certs
      vars:
        mtls_cert_dir: /etc/pykmip/certs
        mtls_cert_group: pykmip
        mtls_ca_common_name: "kmip-ca.example.com"
        mtls_server_common_name: "kmip-server.example.com"
        mtls_client_common_name: "kmip-client.example.com"

  roles:
    - role: ansible-role-kmip
      vars:
        kmip_manage_certificates: false
        kmip_byo_ca_cert_src: "{{ mtls_paths.ca_pem }}"
        kmip_byo_server_cert_src: "{{ mtls_paths.server_pem }}"
        kmip_byo_server_key_src: "{{ mtls_paths.server_key }}"
        kmip_byo_client_cert_src: "{{ mtls_paths.client_pem }}"
        kmip_byo_client_key_src: "{{ mtls_paths.client_key }}"
```

## Testing

### Run Molecule Tests

```bash
# Install dependencies using uv (recommended)
uv pip install --system -r requirements-dev.txt

# Or using standard pip
pip install -r requirements-dev.txt

ansible-galaxy collection install community.crypto community.docker

# Run tests
molecule test
```

### Test Matrix

| Platform | Image |
|----------|-------|
| Rocky Linux 8 | `geerlingguy/docker-rockylinux8-ansible` |
| Rocky Linux 9 | `geerlingguy/docker-rockylinux9-ansible` |
| Ubuntu 22.04 | `geerlingguy/docker-ubuntu2204-ansible` |
| Ubuntu 24.04 | `geerlingguy/docker-ubuntu2404-ansible` |

## License

Apache-2.0

## Author

illuminatus
