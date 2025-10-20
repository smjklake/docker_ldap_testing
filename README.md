# LDAP Docker

A pre-configured OpenLDAP server with SSL/TLS support and test users for the `{.env:LDAP_DOMAIN}` domain.

Perfect for local development and testing of applications that need LDAP authentication without setting up a complex infrastructure. Just run `docker-compose up -d` and you're ready to go!

## Features

- **SSL/TLS Support** - LDAPS on port `{.env:LDAPS_PORT}` with custom certificate support
- **Pre-populated Users** - Test users and groups ready to use
- **Web Admin Interface** - phpLDAPadmin for easy management
- **Docker-based** - Easy deployment with Docker Compose
- **Fully Configurable** - Customize ports, domain, credentials via `.env` file
- **Optional Management Tools** - Makefile and Python scripts for convenience
- **Cross-platform** - Works anywhere Docker runs

> **📝 Note:** Throughout this documentation, values shown as `{.env:VARIABLE_NAME}` indicate they can be customized via environment variables. See [Configuration](#configuration) for details.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Verify Installation](#verify-installation)
- [Custom Certificates (Dev-CA)](#custom-certificates-dev-ca)
- [Usage](#usage)
- [Configuration](#configuration)
- [Test Users](#test-users)
- [Next Steps](#next-steps)
- [Management Tools](#management-tools)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Prerequisites

### Required

- **Docker** - Any provider that can run Docker Compose
  - [Docker Desktop](https://www.docker.com/products/docker-desktop) (Windows, Mac, Linux)
  - [Rancher Desktop](https://rancherdesktop.io/) (Alternative for Mac/Linux)
  - Or native Docker on Linux

- **SSL Certificates** - Either:
  - Generate with the included Python script (requires Python 3.9+)
  - OR bring your own certificates (see [Custom Certificates](#custom-certificates-dev-ca))

That's it! Everything runs in Docker containers.

### Optional Tools

These tools provide convenient shortcuts but are **not required**:

- **Make** - For using `make start` instead of `docker-compose up -d`
- **Python 3.9+** - For certificate generation script and examples
- **UV Package Manager** - Fast Python dependency management
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **OpenSSL** - For manual certificate verification
- **LDAP utilities** - Command-line tools (ldapsearch, ldapadd, etc.)

## Quick Start

### Simple Way (Docker Only)

```bash
# 1. Generate certificates (requires Python)
python3 scripts/generate_certs.py

# 2. Start the server
docker-compose up -d

# 3. View logs
docker-compose logs -f openldap

# 4. Stop the server
docker-compose down
```

That's it! The server is now running at `ldap://localhost:{.env:LDAP_PORT}` and `ldaps://localhost:{.env:LDAPS_PORT}`.

### Convenient Way (Using Make)

If you have Make installed, use these shortcuts:

```bash
# Complete setup (installs Python deps, generates certs, starts server)
make dev-setup

# Or step by step:
make install         # Install Python dependencies
make certs-generate  # Generate SSL certificates
make start           # Start the server
make verify-users    # Verify users are loaded
make logs            # View logs
```

Run `make help` to see all available commands.

### Using Your Own Certificates

Instead of generating certificates, copy yours to the `certs/` directory:

```bash
cp /path/to/ca.crt certs/ca.crt
cp /path/to/server.crt certs/server.crt
cp /path/to/server.key certs/server.key
docker-compose up -d
```

> **💡 Tip:** Want to customize ports, passwords, or domain? Copy `.env.example` to `.env` and edit your settings. See the [Configuration](#configuration) section for details.

## Verify Installation

After starting the server, verify everything is working:

### Test 1: List All Users

```bash
make verify-users
```

You should see output like:

```
Found 4 user(s):

  - Admin User: admin (admin@{.env:LDAP_DOMAIN})
  - John Doe: jdoe (jdoe@{.env:LDAP_DOMAIN})
  - Jane Smith: jsmith (jsmith@{.env:LDAP_DOMAIN})
  - Test User: testuser (testuser@{.env:LDAP_DOMAIN})
```

### Test 2: Try the Web Interface

Open `http://localhost:{.env:PHPLDAPADMIN_PORT}` in your browser and login with:

- **Login DN:** `cn=admin,{.env:LDAP_BASE_DN}`
- **Password:** `{.env:LDAP_ADMIN_PASSWORD}`

### Test 3: Run the Example Script (Optional - Requires Python)

```bash
python examples/simple_auth.py
```

This authenticates user `jdoe` and displays their information.

## Custom Certificates (Dev-CA)

If you wish, you can use your own certificates instead of self-signed ones:

### Using Your Certificates

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

**Important:** The server certificate should be issued for the hostname `{.env:LDAP_HOSTNAME}` or include it as a Subject Alternative Name (SAN).

### Certificate Requirements

The OpenLDAP container expects three files in the `certs/` directory:

- `ca.crt` - Your CA root certificate (filename: `{.env:LDAP_TLS_CA_CRT_FILENAME}`)
- `server.crt` - Server certificate for `{.env:LDAP_HOSTNAME}` (filename: `{.env:LDAP_TLS_CRT_FILENAME}`)
- `server.key` - Private key for the server certificate (filename: `{.env:LDAP_TLS_KEY_FILENAME}`)

### Generating Certificates with Your OpenSSL-based Dev-CA

If your dev-ca is script-based and uses OpenSSL:

```bash
# Example using your dev-ca
cd /path/to/your/dev-ca

# Generate server key
openssl genrsa -out ldap-server.key 4096

# Generate certificate signing request (use your LDAP_HOSTNAME value)
openssl req -new -key ldap-server.key -out ldap-server.csr \
  -subj "/CN={.env:LDAP_HOSTNAME}"

# Sign with your CA (adjust paths as needed)
openssl x509 -req -in ldap-server.csr \
  -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out ldap-server.crt \
  -days 365 -sha256 \
  -extfile <(printf "subjectAltName=DNS:{.env:LDAP_HOSTNAME},DNS:localhost,IP:127.0.0.1")

# Copy to LDAP Docker project
cp ldap-server.crt /path/to/ldap_docker/certs/server.crt
cp ldap-server.key /path/to/ldap_docker/certs/server.key
cp ca-cert.pem /path/to/ldap_docker/certs/ca.crt
```

## Usage

### Accessing the Services

Once started, the following services are available:

| Service      | URL/Connection          | Description                 |
| ------------ | ----------------------- | --------------------------- |
| LDAP         | `ldap://localhost:{.env:LDAP_PORT}`  | Standard LDAP (unencrypted) |
| LDAPS        | `ldaps://localhost:{.env:LDAPS_PORT}` | LDAP over SSL/TLS           |
| phpLDAPadmin | `http://localhost:{.env:PHPLDAPADMIN_PORT}` | Web-based administration    |

### Admin Credentials

- **Admin DN:** `cn=admin,{.env:LDAP_BASE_DN}`
- **Password:** `{.env:LDAP_ADMIN_PASSWORD}`
- **Base DN:** `{.env:LDAP_BASE_DN}`

> **Note:** Default values shown. Customize these by creating a `.env` file (see [Configuration](#configuration)).

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

# Run unit tests
make test

# Verify running server
make verify-all

# Open shell in container
make shell

# Clean up everything
make clean-all
```

## Configuration

You can customize the LDAP server behavior using environment variables. The easiest way is to create a `.env` file in the project root.

### Quick Configuration

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your preferred settings
nano .env  # or vim, code, etc.
```

### Available Configuration Options

The `.env.example` file includes all available options with documentation. Below is a comprehensive reference of all environment variables:

| Variable | Default Value | Description | Usage Reference |
|----------|---------------|-------------|-----------------|
| **Domain & Organization** ||||
| `LDAP_DOMAIN` | `testing.local` | Your LDAP domain | Used in: [Services](#accessing-the-services), [Test Users](#default-test-users) |
| `LDAP_ORGANISATION` | `Testing Organization` | Organization name | Used in LDAP server metadata |
| `LDAP_BASE_DN` | `dc=testing,dc=local` | Base Distinguished Name (auto-derived from domain) | Used in: [Services](#accessing-the-services), [Admin Credentials](#admin-credentials), [Test Users](#default-test-users) |
| **Credentials** ||||
| `LDAP_ADMIN_PASSWORD` | `admin_password` | Admin user password | Used in: [Admin Credentials](#admin-credentials), [Verify Installation](#verify-installation) |
| `LDAP_CONFIG_PASSWORD` | `config_password` | Configuration admin password | Used for LDAP server configuration |
| **Ports** ||||
| `LDAP_PORT` | `389` | Standard LDAP port (unencrypted) | Used in: [Services](#accessing-the-services), [Testing Authentication](#testing-authentication) |
| `LDAPS_PORT` | `636` | LDAPS/SSL port (encrypted) | Used in: [Services](#accessing-the-services), [Testing Authentication](#testing-authentication) |
| `PHPLDAPADMIN_PORT` | `8080` | Web UI port | Used in: [Services](#accessing-the-services), [Verify Installation](#verify-installation) |
| **SSL/TLS** ||||
| `LDAP_TLS` | `true` | Enable TLS support | Controls SSL/TLS functionality |
| `LDAP_TLS_CRT_FILENAME` | `server.crt` | Server certificate filename | Used in: [Custom Certificates](#custom-certificates-dev-ca) |
| `LDAP_TLS_KEY_FILENAME` | `server.key` | Server private key filename | Used in: [Custom Certificates](#custom-certificates-dev-ca) |
| `LDAP_TLS_CA_CRT_FILENAME` | `ca.crt` | CA certificate filename | Used in: [Custom Certificates](#custom-certificates-dev-ca) |
| `LDAP_TLS_VERIFY_CLIENT` | `try` | Client certificate verification mode | Options: `never`, `allow`, `try`, `demand` |
| **Container Configuration** ||||
| `LDAP_HOSTNAME` | `ldap.testing.local` | LDAP server hostname | Used in certificate validation |
| `LDAP_CONTAINER_NAME` | `ldap-server` | LDAP container name | Used in Docker commands |
| `PHPLDAPADMIN_CONTAINER_NAME` | `ldap-admin` | phpLDAPadmin container name | Used in Docker commands |
| **Other Options** ||||
| `LDAP_LOG_LEVEL` | `256` | Logging verbosity | Higher = more verbose |

> **Tip:** Throughout this documentation, values shown as `{.env:VARIABLE_NAME}` indicate they are configured via these environment variables.

#### Summary by Category

##### Domain & Organization
- `LDAP_DOMAIN` - Your LDAP domain (default: `testing.local`)
- `LDAP_ORGANISATION` - Organization name (default: `Testing Organization`)
- `LDAP_BASE_DN` - Base DN, auto-derived from domain if not set

##### Credentials
- `LDAP_ADMIN_PASSWORD` - Admin password (default: `admin_password`)
- `LDAP_CONFIG_PASSWORD` - Config admin password (default: `config_password`)

##### Ports
- `LDAP_PORT` - Standard LDAP port (default: `389`)
- `LDAPS_PORT` - LDAPS/SSL port (default: `636`)
- `PHPLDAPADMIN_PORT` - Web UI port (default: `8080`)

##### SSL/TLS
- `LDAP_TLS` - Enable TLS (default: `true`)
- `LDAP_TLS_CRT_FILENAME` - Server cert filename (default: `server.crt`)
- `LDAP_TLS_KEY_FILENAME` - Server key filename (default: `server.key`)
- `LDAP_TLS_CA_CRT_FILENAME` - CA cert filename (default: `ca.crt`)

##### Container Names
- `LDAP_HOSTNAME` - LDAP server hostname (default: `ldap.testing.local`)
- `LDAP_CONTAINER_NAME` - Container name (default: `ldap-server`)
- `PHPLDAPADMIN_CONTAINER_NAME` - Admin UI container (default: `ldap-admin`)

##### Other Options
- `LDAP_LOG_LEVEL` - Logging verbosity (default: `256`)
- `DEBUG` - Enable debug output (default: `false`)
- `TZ` - Timezone (default: `UTC`)

### Example Custom Configuration

```bash
# .env
LDAP_DOMAIN=mycompany.local
LDAP_ORGANISATION=My Company
LDAP_ADMIN_PASSWORD=mysecurepassword

# Use different ports
LDAP_PORT=1389
LDAPS_PORT=1636
PHPLDAPADMIN_PORT=9080
```

After creating or modifying `.env`, restart the containers:

```bash
docker-compose down
docker-compose up -d
```

For a complete list of options with detailed descriptions, see `.env.example`.

## Default Test Users

The LDAP directory is pre-populated with the following test users:

| Username | Full Name  | Email                            | Password    | UID   |
| -------- | ---------- | -------------------------------- | ----------- | ----- |
| admin    | Admin User | admin@`{.env:LDAP_DOMAIN}`       | password123 | 10000 |
| jdoe     | John Doe   | jdoe@`{.env:LDAP_DOMAIN}`        | password123 | 10001 |
| jsmith   | Jane Smith | jsmith@`{.env:LDAP_DOMAIN}`      | password123 | 10002 |
| testuser | Test User  | testuser@`{.env:LDAP_DOMAIN}`    | password123 | 10003 |

> **Note:** Email addresses are based on `{.env:LDAP_DOMAIN}` (default: `testing.local`). User DNs follow the pattern `uid=username,ou=people,{.env:LDAP_BASE_DN}`.

### Test Groups

- **admins** - Administrator group (member: admin)
- **developers** - Development team (members: jdoe, jsmith)
- **users** - General users (members: jdoe, jsmith, testuser)

### Testing Authentication

```bash
# Test with ldapsearch (using default ports from .env)
ldapsearch -H ldap://localhost:{.env:LDAP_PORT} \
  -D "uid=jdoe,ou=people,{.env:LDAP_BASE_DN}" \
  -w password123 \
  -b "{.env:LDAP_BASE_DN}" \
  "(uid=jdoe)"

# Test LDAPS with SSL
ldapsearch -H ldaps://localhost:{.env:LDAPS_PORT} \
  -D "uid=jdoe,ou=people,{.env:LDAP_BASE_DN}" \
  -w password123 \
  -b "{.env:LDAP_BASE_DN}" \
  "(uid=jdoe)"

# Best practice: Test auth by searching for user's own entry
# This works for all users, not just admin
ldapsearch -H ldap://localhost:{.env:LDAP_PORT} \
  -D "uid=jdoe,ou=people,{.env:LDAP_BASE_DN}" \
  -w password123 \
  -b "uid=jdoe,ou=people,{.env:LDAP_BASE_DN}" \
  -s base \
  "(objectClass=*)"
```

## Next Steps

Now that your LDAP server is running, you can:

### 1. Integrate with Your Application

Point your application to the LDAP server:

- **LDAP URL:** `ldap://localhost:{.env:LDAP_PORT}`
- **LDAPS URL:** `ldaps://localhost:{.env:LDAPS_PORT}`
- **Base DN:** `{.env:LDAP_BASE_DN}`

See `examples/README.md` for code samples and integration patterns.

### 2. Add Custom Users

Edit `ldif/01-users.ldif` to add more users or modify existing ones, then reload:

```bash
make down-volumes  # WARNING: Deletes all data
make start
```

### 3. Customize Configuration

Create a `.env` file to customize ports, credentials, and behavior:

```bash
cp .env.example .env
# Edit .env with your settings
docker-compose down && docker-compose up -d
```

See the [Configuration](#configuration) section for all available options.

### 4. Learn More

- `certs/README.md` - Certificate management guide
- `examples/README.md` - Integration examples and patterns
- [OpenLDAP Documentation](https://www.openldap.org/doc/)

## Management Tools

You can manage the LDAP server using `docker-compose` commands directly, or use the included Makefile for convenience.

### Using Docker Compose (No Additional Tools Required)

```bash
# Server management
docker-compose up -d              # Start server
docker-compose stop               # Stop server
docker-compose restart            # Restart server
docker-compose logs -f openldap   # View logs
docker-compose ps                 # Check status
docker-compose down               # Remove containers
docker-compose down -v            # Remove containers and data

# Generate certificates (requires Python)
python3 scripts/generate_certs.py
```

### Using Make (Optional Convenience)

If you have Make installed, use these shortcuts:

```bash
make help            # View all available commands

# Server management
make start           # Start the LDAP server
make stop            # Stop the LDAP server
make restart         # Restart the LDAP server
make logs            # View server logs
make status          # Check server status

# Certificate management
make certs-generate  # Generate SSL certificates
make certs-check     # Verify SSL certificates

# Unit Testing (requires Python + pytest)
make test            # Run unit tests
make test-cov        # Run tests with coverage

# Verification (requires running container + ldap3)
make verify-connection # Verify LDAP connection
make verify-auth       # Verify authentication
make verify-users      # List all users
make verify-all        # Run all verification checks

# Setup
make install         # Install Python dependencies
make dev-setup       # Complete development setup

# Cleanup
make clean           # Clean build artifacts
make down-volumes    # Remove containers and data
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
telnet localhost {.env:LDAP_PORT}
```

**Problem:** Authentication fails

```bash
# Verify credentials
# Default admin: cn=admin,{.env:LDAP_BASE_DN} / {.env:LDAP_ADMIN_PASSWORD}

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
dn: uid=newuser,ou=people,{.env:LDAP_BASE_DN}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: newuser
cn: New User
sn: User
mail: newuser@{.env:LDAP_DOMAIN}
userPassword: {SSHA}5en6G6MezRroT3XKqkdPOmY/BFQ=
uidNumber: 10004
gidNumber: 10004
homeDirectory: /home/newuser
loginShell: /bin/bash
```

> **Note:** Replace `{.env:LDAP_BASE_DN}` and `{.env:LDAP_DOMAIN}` with your actual values from the `.env` file (defaults: `dc=testing,dc=local` and `testing.local`).

Then restart with fresh data:

```bash
make down-volumes
make start
```

### Modifying Configuration

The easiest way to customize settings is with a `.env` file:

```bash
cp .env.example .env
# Edit .env with your preferences
docker-compose down && docker-compose up -d
```

See `.env.example` for all available options with detailed documentation, or the [Configuration](#configuration) section.

For advanced customization, you can also edit `docker-compose.yml` to change volume mounts, resource limits, or other Docker-specific settings.

### Python Development (Optional)

If you're contributing to the Python scripts:

```bash
# Install development dependencies (requires UV)
make install-dev

# Run tests
uv run pytest

# Format and lint code
ruff format scripts/
ruff check scripts/
```

### Cross-Platform Compatibility

This project uses standard Docker images and docker-compose.yml format, so it works anywhere Docker runs:

- **Linux** - Native Docker
- **MacOS** - Docker Desktop, Rancher Desktop, or Colima
- **Windows** - Docker Desktop (with WSL2)

No platform-specific code or configuration needed!

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
