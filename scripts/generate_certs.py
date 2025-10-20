#!/usr/bin/env python3
"""
Generate self-signed SSL/TLS certificates for LDAP server testing.

This script creates a CA certificate and a server certificate for development use.
For production, use proper certificates from your dev-ca or a trusted CA.
"""

import argparse
import ipaddress
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
except ImportError:
    print("Error: cryptography library not found.")
    print("Install it with: uv pip install cryptography")
    sys.exit(1)


def generate_private_key(key_size: int = 4096) -> rsa.RSAPrivateKey:
    """Generate an RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend(),
    )


def generate_ca_certificate(
    private_key: rsa.RSAPrivateKey,
    common_name: str = "Testing CA",
    days_valid: int = 3650,
) -> x509.Certificate:
    """Generate a self-signed CA certificate."""
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Testing Organization"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days_valid))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    return certificate


def generate_server_certificate(
    private_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    ca_key: rsa.RSAPrivateKey,
    hostname: str = "ldap.testing.local",
    san_list: list[str] | None = None,
    days_valid: int = 365,
) -> x509.Certificate:
    """Generate a server certificate signed by the CA."""
    if san_list is None:
        san_list = [
            "ldap.testing.local",
            "localhost",
        ]

    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Testing Organization"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ]
    )

    # Build Subject Alternative Names
    san_entries = []
    for name in san_list:
        san_entries.append(x509.DNSName(name))
    # Add IP addresses
    san_entries.append(x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")))

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days_valid))
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256(), default_backend())
    )

    return certificate


def save_private_key(key: rsa.RSAPrivateKey, filepath: Path) -> None:
    """Save a private key to a file."""
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    filepath.write_bytes(pem)
    filepath.chmod(0o600)  # Set restrictive permissions
    print(f"✓ Private key saved: {filepath}")


def save_certificate(cert: x509.Certificate, filepath: Path) -> None:
    """Save a certificate to a file."""
    pem = cert.public_bytes(serialization.Encoding.PEM)
    filepath.write_bytes(pem)
    filepath.chmod(0o644)
    print(f"✓ Certificate saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SSL/TLS certificates for LDAP development server"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "certs",
        help="Output directory for certificates (default: ./certs)",
    )
    parser.add_argument(
        "--hostname",
        default="ldap.testing.local",
        help="Server hostname (default: ldap.testing.local)",
    )
    parser.add_argument(
        "--san",
        action="append",
        help="Additional Subject Alternative Names (can be used multiple times)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing certificates",
    )
    parser.add_argument(
        "--ca-days",
        type=int,
        default=3650,
        help="CA certificate validity in days (default: 3650)",
    )
    parser.add_argument(
        "--server-days",
        type=int,
        default=365,
        help="Server certificate validity in days (default: 365)",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Define file paths
    ca_key_path = args.output_dir / "ca.key"
    ca_cert_path = args.output_dir / "ca.crt"
    server_key_path = args.output_dir / "server.key"
    server_cert_path = args.output_dir / "server.crt"

    # Check if certificates already exist
    if not args.force:
        existing = [p for p in [ca_cert_path, server_cert_path, server_key_path] if p.exists()]
        if existing:
            print("Error: The following certificate files already exist:")
            for p in existing:
                print(f"  - {p}")
            print("\nUse --force to overwrite existing certificates")
            sys.exit(1)

    print("Generating certificates for LDAP server...")
    print(f"Hostname: {args.hostname}")
    print(f"Output directory: {args.output_dir}")
    print()

    # Generate CA
    print("Step 1: Generating CA certificate...")
    ca_key = generate_private_key()
    ca_cert = generate_ca_certificate(ca_key, days_valid=args.ca_days)
    save_private_key(ca_key, ca_key_path)
    save_certificate(ca_cert, ca_cert_path)
    print()

    # Generate Server Certificate
    print("Step 2: Generating server certificate...")
    server_key = generate_private_key()

    san_list = [args.hostname, "localhost"]
    if args.san:
        san_list.extend(args.san)

    server_cert = generate_server_certificate(
        server_key,
        ca_cert,
        ca_key,
        hostname=args.hostname,
        san_list=san_list,
        days_valid=args.server_days,
    )
    save_private_key(server_key, server_key_path)
    save_certificate(server_cert, server_cert_path)
    print()

    print("✅ Certificate generation complete!")
    print()
    print("Generated files:")
    print(f"  - CA Certificate: {ca_cert_path}")
    print(f"  - CA Private Key: {ca_key_path} (keep secure!)")
    print(f"  - Server Certificate: {server_cert_path}")
    print(f"  - Server Private Key: {server_key_path} (keep secure!)")
    print()
    print("Next steps:")
    print("  1. Keep the CA private key secure (you can delete it if not needed)")
    print("  2. Start the LDAP server: docker-compose up -d")
    print("  3. Test the connection: ldapsearch -H ldaps://localhost:636 -x")
    print()
    print("Note: These certificates are for DEVELOPMENT ONLY!")


if __name__ == "__main__":
    main()
