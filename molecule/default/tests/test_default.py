"""
Testinfra tests for mTLS Certificate role
Tests infrastructure state, file permissions, and certificate attributes
"""

import pytest


# =============================================================================
# File Existence Tests
# =============================================================================

@pytest.mark.parametrize("path", [
    "/etc/pki/mtls",
    "/etc/pki/mtls/ca",
    "/etc/pki/mtls/server",
    "/etc/pki/mtls/client",
])
def test_directories_exist(host, path):
    """Verify all required directories exist."""
    directory = host.file(path)
    assert directory.exists, f"Directory {path} should exist"
    assert directory.is_directory, f"{path} should be a directory"


@pytest.mark.parametrize("path", [
    "/etc/pki/mtls/ca/ca.pem",
    "/etc/pki/mtls/ca/ca.key",
    "/etc/pki/mtls/ca/ca.csr",
    "/etc/pki/mtls/server/server.pem",
    "/etc/pki/mtls/server/server.key",
    "/etc/pki/mtls/server/server.csr",
    "/etc/pki/mtls/client/client.pem",
    "/etc/pki/mtls/client/client.key",
    "/etc/pki/mtls/client/client.csr",
])
def test_files_exist(host, path):
    """Verify all required files exist."""
    file = host.file(path)
    assert file.exists, f"File {path} should exist"
    assert file.is_file, f"{path} should be a regular file"


# =============================================================================
# File Permission Tests
# =============================================================================

def test_base_directory_permissions(host):
    """Verify /etc/pki/mtls has correct ownership and permissions."""
    directory = host.file("/etc/pki/mtls")
    assert directory.user == "root"
    assert directory.group == "root"
    assert directory.mode == 0o750


@pytest.mark.parametrize("path", [
    "/etc/pki/mtls/ca",
    "/etc/pki/mtls/server",
    "/etc/pki/mtls/client",
])
def test_cert_directory_permissions(host, path):
    """Verify certificate directories have correct permissions."""
    directory = host.file(path)
    assert directory.user == "root", f"{path} should be owned by root"
    assert directory.group == "root", f"{path} should have group root"
    assert directory.mode == 0o750, f"{path} should have mode 0750"


@pytest.mark.parametrize("path", [
    "/etc/pki/mtls/ca/ca.key",
    "/etc/pki/mtls/server/server.key",
    "/etc/pki/mtls/client/client.key",
])
def test_private_key_permissions(host, path):
    """Verify private keys have restricted permissions."""
    key = host.file(path)
    assert key.user == "root", f"{path} should be owned by root"
    assert key.group == "root", f"{path} should have group root"
    assert key.mode == 0o640, f"{path} should have mode 0640"


@pytest.mark.parametrize("path", [
    "/etc/pki/mtls/ca/ca.pem",
    "/etc/pki/mtls/server/server.pem",
    "/etc/pki/mtls/client/client.pem",
])
def test_certificate_permissions(host, path):
    """Verify certificates have correct permissions."""
    cert = host.file(path)
    assert cert.user == "root"
    assert cert.group == "root"
    assert cert.mode == 0o644


# =============================================================================
# Certificate Attribute Tests
# =============================================================================

def test_ca_certificate_attributes(host):
    """Verify CA certificate has correct attributes."""
    cert_path = "/etc/pki/mtls/ca/ca.pem"
    cert_file = host.file(cert_path)
    
    # Verify it's a certificate
    assert "BEGIN CERTIFICATE" in cert_file.content_string
    assert "END CERTIFICATE" in cert_file.content_string

    # Check subject CN via openssl
    cmd = host.run(f"openssl x509 -noout -subject -in {cert_path}")
    assert cmd.rc == 0
    assert "CN = test-ca.example.com" in cmd.stdout or "CN=test-ca.example.com" in cmd.stdout


def test_server_certificate_attributes(host):
    """Verify server certificate has correct attributes."""
    cert_path = "/etc/pki/mtls/server/server.pem"
    cert_file = host.file(cert_path)

    # Verify it's a certificate
    assert "BEGIN CERTIFICATE" in cert_file.content_string
    assert "END CERTIFICATE" in cert_file.content_string

    # Check subject CN via openssl
    cmd = host.run(f"openssl x509 -noout -subject -in {cert_path}")
    assert cmd.rc == 0
    assert "CN = test-server.example.com" in cmd.stdout or "CN=test-server.example.com" in cmd.stdout


def test_client_certificate_attributes(host):
    """Verify client certificate has correct attributes."""
    cert_path = "/etc/pki/mtls/client/client.pem"
    cert_file = host.file(cert_path)

    # Verify it's a certificate
    assert "BEGIN CERTIFICATE" in cert_file.content_string
    assert "END CERTIFICATE" in cert_file.content_string

    # Check subject CN via openssl
    cmd = host.run(f"openssl x509 -noout -subject -in {cert_path}")
    assert cmd.rc == 0
    assert "CN = test-client.example.com" in cmd.stdout or "CN=test-client.example.com" in cmd.stdout


def test_certificate_key_sizes(host):
    """Verify certificate key sizes using openssl."""
    # CA should be 4096-bit
    ca_key_check = host.run(
        "openssl rsa -in /etc/pki/mtls/ca/ca.key -text -noout | grep 'Private-Key:'"
    )
    assert "4096 bit" in ca_key_check.stdout

    # Server should be 2048-bit
    server_key_check = host.run(
        "openssl rsa -in /etc/pki/mtls/server/server.key -text -noout | grep 'Private-Key:'"
    )
    assert "2048 bit" in server_key_check.stdout

    # Client should be 2048-bit
    client_key_check = host.run(
        "openssl rsa -in /etc/pki/mtls/client/client.key -text -noout | grep 'Private-Key:'"
    )
    assert "2048 bit" in client_key_check.stdout


def test_server_certificate_san(host):
    """Verify server certificate has Subject Alternative Name."""
    san_check = host.run(
        "openssl x509 -in /etc/pki/mtls/server/server.pem -text -noout | "
        "grep -A1 'Subject Alternative Name'"
    )
    assert san_check.rc == 0, "Server certificate should have SAN"


# =============================================================================
# Security Tests
# =============================================================================

def test_no_world_writable_files(host):
    """Verify no world-writable files in certificate directories."""
    result = host.run("find /etc/pki/mtls -type f -perm -002 2>/dev/null")
    assert result.stdout.strip() == "", "No files should be world-writable"


def test_private_keys_not_world_readable(host):
    """Verify private keys are not world-readable."""
    for key_path in [
        "/etc/pki/mtls/ca/ca.key",
        "/etc/pki/mtls/server/server.key",
        "/etc/pki/mtls/client/client.key",
    ]:
        key = host.file(key_path)
        # Mode 0o640 means not world-readable (no 0o004 bit)
        assert (key.mode & 0o004) == 0, f"{key_path} should not be world-readable"
