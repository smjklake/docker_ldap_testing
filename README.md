# LDAP Docker

This is a development tool project that, when deployed, offers an SSL-capable OpenLDAP server populated with test users for a fictional `testing.local` domain.

Perfect for local development and testing of applications that need LDAP authentication without setting up a complex infrastructure.

## Features

- 🔒 **SSL/TLS Support** - LDAPS on port 636 with custom certificate support
- 👥 **Pre-populated Users** - Test users and groups ready to use
- 🌐 **Web Admin Interface** - phpLDAPadmin for easy management
- 🐳 **Docker-based** - Easy deployment with Docker Compose
- 🔧 **Python Management Tools** - UV-based CLI for convenience
- 🍎 **Cross-platform** - Works on MacOS (Rancher Desktop), Linux, and Windows

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Custom Certificates (Dev-CA)](#custom-certificates-dev-ca)
- [Usage](#usage)
- [Test Users](#test-users)
- [Management Tools](#management-tools)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Prerequisites

### Required

- **Docker** or **Rancher Desktop** (recommended for MacOS)
  - MacOS: [Download Rancher Desktop](https://rancherdesktop.io/)
  - Alternatively: [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Python 3.9+** (for management scripts)
- **UV Package Manager** (recommended)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Optional

- **OpenSSL** (for certificate verification)
- **LDAP utilities** (ldapsearch, ldapadd, etc.) for testing

## Quick Start

### Option 1: Using Make (Recommended)

```bash
# 1. Install dependencies
make install

# 2. Generate certificates (or copy your own - see below)
make certs-generate

# 3. Start the server
make start

# 4. Test the connection
make test-connection

# 5. List users
make test-users
```

### Option 2: Using Docker Compose Directly

```bash
# 1. Generate certificates
python scripts/generate_certs.py

# 2. Start services
docker-compose up -d

# 3. View logs
docker-compose logs -f openldap
```

### Option 3: Complete Dev Setup

This will install everything, generate certificates, and start the server:

```bash
make dev-setup
```

## Custom Certificates (Dev-CA)

If you maintain your own dev-ca (as mentioned), you can use your own certificates instead of self-signed ones:

### Using Your Dev-CA Certificates

```bash
# Copy your certificates to the certs directory
cp /path/to/your/dev-ca/certs/ldap-server.crt certs/server.crt
cp /path/to/your/dev-ca/private/ldap-server.key certs/server.key
cp /path/to/your/dev-ca/ca-cert.pem certs/ca.crt

# Ensure proper permissions
chmod 644 certs/ca.crt
chmod 644 certs/server.crt
chmod 600 certs/server.key
```

**Important:** The server certificate should be issued for the hostname `ldap.testing.local` or include it as a Subject Alternative Name (SAN).

### Certificate Requirements

The OpenLDAP container expects three files in the `certs/` directory:

- `ca.crt` - Your CA root certificate
- `server.crt` - Server certificate for ldap.testing.local
- `server.key` - Private key for the server certificate

### Generating Certificates with Your OpenSSL-based Dev-CA

If your dev-ca is script-based and uses OpenSSL:

```bash
# Example using your dev-ca
cd /path/to/your/dev-ca

# Generate server key
openssl genrsa -out ldap-server.key 4096

# Generate certificate signing request
openssl req -new -key ldap-server.key -out ldap-server.csr \
  -subj "/CN=ldap.testing.local"

# Sign with your CA (adjust paths as needed)
openssl x509 -req -in ldap-server.csr \
  -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out ldap-server.crt \
  -days 365 -sha256 \
  -extfile <(printf "subjectAltName=DNS:ldap.testing.local,DNS:localhost,IP:127.0.0.1")

# Copy to LDAP Docker project
cp ldap-server.crt /path/to/ldap_docker/certs/server.crt
cp ldap-server.key /path/to/ldap_docker/certs/server.key
cp ca-cert.pem /path/to/ldap_docker/certs/ca.crt
```

## Usage

### Accessing the Services

Once started, the following services are available:

| Service | URL/Connection | Description |
|---------|----------------|-------------|
| LDAP | `ldap://localhost:389` | Standard LDAP (unencrypted) |
| LDAPS | `ldaps://localhost:636` | LDAP over SSL/TLS |
| phpLDAPadmin | `http://localhost:8080` | Web-based administration |

### Admin Credentials

- **Admin DN:** `cn=admin,dc=testing,dc=local`
- **Password:** `admin_password`
- **Base DN:** `dc=testing,dc=local`

### Common Commands

```bash
# Start the server
make start

# Stop the server
make stop

# View logs
make logs

# Check status
make status

# Run tests
make test-all

# Open shell in container
make shell

# Clean up everything
make clean-all
```

## Test Users

The LDAP directory is pre-populated with the following test users:

| Username | Full Name | Email | Password | UID |
|----------|-----------|-------|----------|-----|
| admin | Admin User | admin@testing.local | password123 | 10000 |
| jdoe | John Doe | jdoe@testing.local | password123 | 10001 |
| jsmith | Jane Smith | jsmith@testing.local | password123 | 10002 |
| testuser | Test User | testuser@testing.local | password123 | 10003 |

### Test Groups

- **admins** - Administrator group (member: admin)
- **developers** - Development team (members: jdoe, jsmith)
- **users** - General users (members: jdoe, jsmith, testuser)

### Testing Authentication

```bash
# Test with ldapsearch
ldapsearch -H ldap://localhost:389 \
  -D "uid=jdoe,ou=people,dc=testing,dc=local" \
  -w password123 \
  -b "dc=testing,dc=local" \
  "(uid=jdoe)"

# Test LDAPS with SSL
ldapsearch -H ldaps://localhost:636 \
  -D "uid=jdoe,ou=people,dc=testing,dc=local" \
  -w password123 \
  -b "dc=testing,dc=local" \
  "(uid=jdoe)"
```

## Management Tools

This project includes Python-based management tools using UV.

### Installation

```bash
# Install dependencies with UV
make install

# Or manually
uv sync
```

### CLI Tool Usage

```bash
# View available commands
uv run ldap-docker --help

# Server management
uv run ldap-docker server start
uv run ldap-docker server stop
uv run ldap-docker server logs -f

# Certificate management
uv run ldap-docker certs generate
uv run ldap-docker certs check

# Testing
uv run ldap-docker test connection
uv run ldap-docker test auth
uv run ldap-docker test users

# Initialize environment
uv run ldap-docker init
```

## Project Structure

```
ldap_docker/
├── certs/                    # SSL/TLS certificates (git-ignored)
│   ├── README.md            # Certificate documentation
│   ├── ca.crt               # CA certificate (your dev-ca)
│   ├── server.crt           # Server certificate
│   └── server.key           # Server private key
├── ldif/                     # LDAP Data Interchange Format files
│   └── 01-users.ldif        # Initial user and group data
├── scripts/                  # Management scripts
│   ├── cli.py               # CLI tool for managing LDAP
│   └── generate_certs.py    # Certificate generation utility
├── docker-compose.yml        # Docker Compose configuration
├── pyproject.toml           # Python project configuration (UV)
├── Makefile                 # Convenient command shortcuts
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Troubleshooting

### Docker/Rancher Desktop Issues

**Problem:** `docker` command not found

```bash
# For Rancher Desktop on MacOS, ensure it's running and configured
# Check Docker settings in Rancher Desktop preferences
```

**Problem:** Cannot connect to Docker daemon

```bash
# Ensure Rancher Desktop or Docker Desktop is running
# On MacOS: Check if Rancher Desktop is in the menu bar
```

### Certificate Issues

**Problem:** LDAPS connection fails with certificate error

```bash
# Verify certificates exist
make certs-check

# Check certificate details
openssl x509 -in certs/server.crt -text -noout

# Verify certificate chain
openssl verify -CAfile certs/ca.crt certs/server.crt
```

**Problem:** Wrong hostname in certificate

```bash
# Regenerate with correct hostname
make certs-generate

# Or copy certificates from your dev-ca with correct hostname
```

### Connection Issues

**Problem:** Cannot connect to LDAP server

```bash
# Check if containers are running
docker-compose ps

# View logs for errors
make logs

# Test basic connectivity
telnet localhost 389
```

**Problem:** Authentication fails

```bash
# Verify credentials
# Default admin: cn=admin,dc=testing,dc=local / admin_password

# Check LDAP logs
docker-compose logs openldap | grep -i error
```

### Data Issues

**Problem:** Users not appearing

```bash
# Check if LDIF files were loaded
docker-compose logs openldap | grep -i ldif

# Restart and reload
make down-volumes  # WARNING: Deletes data
make start
```

## Development

### Adding Custom Users

Edit `ldif/01-users.ldif` to add more users or modify existing ones:

```ldif
dn: uid=newuser,ou=people,dc=testing,dc=local
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: newuser
cn: New User
sn: User
mail: newuser@testing.local
userPassword: {SSHA}5en6G6MezRroT3XKqkdPOmY/BFQ=
uidNumber: 10004
gidNumber: 10004
homeDirectory: /home/newuser
loginShell: /bin/bash
```

Then restart with fresh data:

```bash
make down-volumes
make start
```

### Modifying Configuration

Edit `docker-compose.yml` to change:
- Port mappings
- Environment variables
- Volume mounts
- Resource limits

### Python Development

```bash
# Install development dependencies
make install-dev

# Run tests
uv run pytest

# Format code
uv run black scripts/

# Lint code
uv run ruff check scripts/

# Type check
uv run mypy scripts/
```

### Building on Other Platforms

This project is designed to work on:
- **MacOS** (with Rancher Desktop or Docker Desktop)
- **Linux** (with Docker and Docker Compose)
- **Windows** (with Docker Desktop and WSL2)

The `docker-compose.yml` uses standard Docker images and should work anywhere Docker runs.

## Security Notes

⚠️ **This is a development tool only!**

- Default passwords are weak and well-known
- Self-signed certificates are not trusted
- No backup or disaster recovery
- No monitoring or alerting
- Not hardened for production use

**Never use this in production or with real user data!**

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! This is a development tool, so:
1. Keep it simple and easy to use
2. Maintain cross-platform compatibility
3. Update documentation for any changes
4. Test with both Docker Desktop and Rancher Desktop

## Resources

- [OpenLDAP Documentation](https://www.openldap.org/doc/)
- [LDAP on Docker Hub](https://hub.docker.com/r/osixia/openldap)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [LDAP Tools Guide](https://www.openldap.org/doc/admin24/quickstart.html)

---

**Need Help?** Check the [Troubleshooting](#troubleshooting) section or view logs with `make logs`
