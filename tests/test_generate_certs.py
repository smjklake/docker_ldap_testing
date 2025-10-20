"""
Tests for certificate generation script.

This module contains unit tests for the generate_certs.py script.
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509 import BasicConstraints, SubjectAlternativeName
    from cryptography.x509.oid import ExtensionOID, NameOID

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    if TYPE_CHECKING:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509 import BasicConstraints, SubjectAlternativeName
        from cryptography.x509.oid import ExtensionOID, NameOID

# Import the module to test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

if CRYPTO_AVAILABLE or TYPE_CHECKING:
    from scripts.generate_certs import (
        generate_ca_certificate,
        generate_private_key,
        generate_server_certificate,
        save_certificate,
        save_private_key,
    )


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography library not available")
class TestCertificateGeneration:
    """Tests for certificate generation functions."""

    def test_generate_private_key(self):
        """Test that a private key can be generated."""
        key = generate_private_key(key_size=2048)
        assert isinstance(key, rsa.RSAPrivateKey)
        assert key.key_size == 2048

    def test_generate_private_key_default_size(self):
        """Test that default key size is 4096."""
        key = generate_private_key()
        assert isinstance(key, rsa.RSAPrivateKey)
        assert key.key_size == 4096

    def test_generate_ca_certificate(self):
        """Test that a CA certificate can be generated."""
        key = generate_private_key(key_size=2048)
        cert = generate_ca_certificate(key, common_name="Test CA", days_valid=365)

        assert isinstance(cert, x509.Certificate)
        assert cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == "Test CA"

        # Check that it's self-signed
        assert cert.subject == cert.issuer

        # Check basic constraints
        basic_constraints = cert.extensions.get_extension_for_oid(ExtensionOID.BASIC_CONSTRAINTS)
        assert cast(BasicConstraints, basic_constraints.value).ca is True

    def test_generate_ca_certificate_validity(self):
        """Test that CA certificate has correct validity period."""
        key = generate_private_key(key_size=2048)
        days_valid = 365
        cert = generate_ca_certificate(key, days_valid=days_valid)

        now = datetime.now(timezone.utc)
        expected_expiry = now + timedelta(days=days_valid)

        # Allow 1 minute tolerance for test execution time
        assert abs((cert.not_valid_after_utc - expected_expiry).total_seconds()) < 60

    def test_generate_server_certificate(self):
        """Test that a server certificate can be generated."""
        ca_key = generate_private_key(key_size=2048)
        ca_cert = generate_ca_certificate(ca_key, common_name="Test CA")

        server_key = generate_private_key(key_size=2048)
        server_cert = generate_server_certificate(
            server_key,
            ca_cert,
            ca_key,
            hostname="test.example.com",
            days_valid=365,
        )

        assert isinstance(server_cert, x509.Certificate)
        assert (
            server_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            == "test.example.com"
        )

        # Check that it's signed by the CA
        assert server_cert.issuer == ca_cert.subject

        # Check basic constraints - should not be a CA
        basic_constraints = server_cert.extensions.get_extension_for_oid(
            ExtensionOID.BASIC_CONSTRAINTS
        )
        assert cast(BasicConstraints, basic_constraints.value).ca is False

    def test_generate_server_certificate_san(self):
        """Test that server certificate includes Subject Alternative Names."""
        ca_key = generate_private_key(key_size=2048)
        ca_cert = generate_ca_certificate(ca_key)

        server_key = generate_private_key(key_size=2048)
        san_list = ["test.example.com", "localhost", "test.local"]
        server_cert = generate_server_certificate(
            server_key,
            ca_cert,
            ca_key,
            hostname="test.example.com",
            san_list=san_list,
        )

        # Get SAN extension
        san_ext = server_cert.extensions.get_extension_for_oid(
            ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )

        # Extract DNS names
        dns_names = [
            name.value
            for name in cast(SubjectAlternativeName, san_ext.value)
            if isinstance(name, x509.DNSName)
        ]

        # Check that all DNS names are present
        for name in san_list:
            assert name in dns_names

    def test_save_private_key(self):
        """Test that a private key can be saved to a file."""
        key = generate_private_key(key_size=2048)

        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / "test.key"
            save_private_key(key, key_path)

            assert key_path.exists()
            assert key_path.stat().st_size > 0

            # Check file permissions (on Unix-like systems)
            if hasattr(key_path.stat(), "st_mode"):
                mode = key_path.stat().st_mode & 0o777
                assert mode == 0o600, f"Expected 0o600 but got {oct(mode)}"

    def test_save_certificate(self):
        """Test that a certificate can be saved to a file."""
        key = generate_private_key(key_size=2048)
        cert = generate_ca_certificate(key)

        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = Path(tmpdir) / "test.crt"
            save_certificate(cert, cert_path)

            assert cert_path.exists()
            assert cert_path.stat().st_size > 0

            # Check file permissions
            if hasattr(cert_path.stat(), "st_mode"):
                mode = cert_path.stat().st_mode & 0o777
                assert mode == 0o644, f"Expected 0o644 but got {oct(mode)}"

    def test_full_certificate_chain(self):
        """Test generating a complete certificate chain."""
        # Generate CA
        ca_key = generate_private_key(key_size=2048)
        ca_cert = generate_ca_certificate(ca_key, common_name="Test Root CA")

        # Generate server certificate
        server_key = generate_private_key(key_size=2048)
        server_cert = generate_server_certificate(
            server_key,
            ca_cert,
            ca_key,
            hostname="ldap.testing.local",
            san_list=["ldap.testing.local", "localhost"],
        )

        # Verify the chain
        assert server_cert.issuer == ca_cert.subject
        assert ca_cert.subject == ca_cert.issuer  # Self-signed

        # Verify server cert is not a CA
        server_basic_constraints = server_cert.extensions.get_extension_for_oid(
            ExtensionOID.BASIC_CONSTRAINTS
        )
        assert cast(BasicConstraints, server_basic_constraints.value).ca is False

        # Verify CA cert is a CA
        ca_basic_constraints = ca_cert.extensions.get_extension_for_oid(
            ExtensionOID.BASIC_CONSTRAINTS
        )
        assert cast(BasicConstraints, ca_basic_constraints.value).ca is True


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography library not available")
class TestCertificateValidation:
    """Tests for certificate validation and properties."""

    def test_certificate_has_correct_extensions(self):
        """Test that generated certificates have correct extensions."""
        ca_key = generate_private_key(key_size=2048)
        ca_cert = generate_ca_certificate(ca_key)

        server_key = generate_private_key(key_size=2048)
        server_cert = generate_server_certificate(
            server_key, ca_cert, ca_key, hostname="test.local"
        )

        # Check server certificate extensions
        ext_oids = [ext.oid for ext in server_cert.extensions]

        assert ExtensionOID.SUBJECT_ALTERNATIVE_NAME in ext_oids
        assert ExtensionOID.BASIC_CONSTRAINTS in ext_oids
        assert ExtensionOID.KEY_USAGE in ext_oids
        assert ExtensionOID.EXTENDED_KEY_USAGE in ext_oids
        assert ExtensionOID.SUBJECT_KEY_IDENTIFIER in ext_oids
        assert ExtensionOID.AUTHORITY_KEY_IDENTIFIER in ext_oids

    def test_certificate_validity_dates(self):
        """Test that certificates have correct validity dates."""
        key = generate_private_key(key_size=2048)
        days_valid = 100
        cert = generate_ca_certificate(key, days_valid=days_valid)

        now = datetime.now(timezone.utc)

        # Check not_valid_before is around now
        assert abs((cert.not_valid_before_utc - now).total_seconds()) < 60

        # Check not_valid_after is around now + days_valid
        expected_expiry = now + timedelta(days=days_valid)
        assert abs((cert.not_valid_after_utc - expected_expiry).total_seconds()) < 60


def test_imports():
    """Test that all required imports are available."""
    if CRYPTO_AVAILABLE:
        assert x509 is not None
        assert hashes is not None
        assert rsa is not None
    else:
        pytest.skip("cryptography library not available")
