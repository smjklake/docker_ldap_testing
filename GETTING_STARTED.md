# Getting Started with LDAP Docker

Welcome! This guide will help you get your LDAP development server up and running in just a few minutes.

## What is This?

LDAP Docker is a ready-to-use OpenLDAP server for development and testing. It comes pre-configured with:

- ✅ SSL/TLS support (LDAPS)
- ✅ Test users and groups
- ✅ Web-based admin interface
- ✅ Easy certificate management
- ✅ Simple Python CLI tools

Perfect for testing applications that need LDAP authentication without setting up a complex infrastructure.

## Prerequisites

You'll need these installed on your Mac:

1. **Docker or Rancher Desktop** (for running containers)
   - Rancher Desktop: https://rancherdesktop.io/ (recommended for Mac)
   - Or Docker Desktop: https://www.docker.com/products/docker-desktop

2. **Python 3.9+** (usually pre-installed on Mac)
   ```bash
   python3 --version
   ```

3. **UV Package Manager** (optional but recommended)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Quick Start (5 Minutes)

### Option 1: Automated Setup (Easiest)

Run the quick start script that will guide you through everything:

```bash
./quickstart.sh
```

This interactive script will:
1. Check all prerequisites
2. Install UV (if you want)
3. Generate SSL certificates
4. Start the LDAP server
5. Verify everything works

### Option 2: Manual Setup (Step by Step)

If you prefer to understand each step:

```bash
# 1. Install Python dependencies
make install

# 2. Generate SSL certificates
make certs-generate

# 3. Start the LDAP server
make start

# 4. Test the connection
make test-connection
```

That's it! Your LDAP server is now running.

## Using Your Own Dev-CA Certificates

Since you mentioned you maintain a local dev-ca, here's how to use your own certificates:

```bash
# Instead of 'make certs-generate', copy your certificates:
cp /path/to/your/dev-ca/ca-cert.pem certs/ca.crt
cp /path/to/your/dev-ca/ldap-server.crt certs/server.crt
cp /path/to/your/dev-ca/ldap-server.key certs/server.key

# Set proper permissions
chmod 644 certs/ca.crt certs/server.crt
chmod 600 certs/server.key

# Then start the server
make start
```

**Important:** Your server certificate should be issued for hostname `ldap.testing.local` or include it as a Subject Alternative Name (SAN).

## Accessing Your LDAP Server

Once running, you can access:

| Service | URL | Purpose |
|---------|-----|---------|
| **LDAP** | `ldap://localhost:389` | Standard LDAP (unencrypted) |
| **LDAPS** | `ldaps://localhost:636` | Secure LDAP with SSL/TLS |
| **Admin UI** | `http://localhost:8080` | Web interface (phpLDAPadmin) |

### Login Credentials

- **Admin DN:** `cn=admin,dc=testing,dc=local`
- **Password:** `admin_password`

### Test Users (All use password: `password123`)

- `jdoe` - John Doe (jdoe@testing.local)
- `jsmith` - Jane Smith (jsmith@testing.local)
- `testuser` - Test User (testuser@testing.local)
- `admin` - Admin User (admin@testing.local)

## Verify Everything Works

### Test 1: List all users
```bash
make test-users
```

You should see output like:
```
Found 4 user(s):

  - Admin User: admin (admin@testing.local)
  - John Doe: jdoe (jdoe@testing.local)
  - Jane Smith: jsmith (jsmith@testing.local)
  - Test User: testuser (testuser@testing.local)
```

### Test 2: Try the web interface

Open http://localhost:8080 in your browser and login with:
- Login DN: `cn=admin,dc=testing,dc=local`
- Password: `admin_password`

### Test 3: Run the example script

```bash
python examples/simple_auth.py
```

This authenticates user `jdoe` and displays their information.

## Common Commands

```bash
# Server management
make start          # Start LDAP server
make stop           # Stop LDAP server
make restart        # Restart LDAP server
make logs           # View logs (live)
make status         # Check if running

# Testing
make test-users     # List all users
make test-auth      # Test authentication
make test-all       # Run all tests

# Maintenance
make clean          # Clean build artifacts
make down           # Stop and remove containers
```

## Next Steps

Now that your LDAP server is running, you can:

1. **Integrate with Your Application**
   - See `examples/README.md` for code samples
   - Point your app to `ldap://localhost:389`

2. **Add Custom Users**
   - Edit `ldif/01-users.ldif`
   - Run `make down-volumes && make start` to reload

3. **Configure for Your Use Case**
   - Edit `docker-compose.yml` for custom settings
   - See `.env.example` for environment variables

4. **Learn More**
   - `README.md` - Full documentation
   - `QUICKREF.md` - Command reference
   - `certs/README.md` - Certificate management
   - `examples/README.md` - Integration examples

## Troubleshooting

### "Docker is not running"
Start Rancher Desktop from your Applications folder. Look for its icon in the menu bar.

### "Connection refused"
Wait 10-30 seconds after starting - the server needs time to initialize:
```bash
make logs  # Watch until you see "slapd starting"
```

### "Certificate errors"
Verify certificates exist:
```bash
ls -la certs/
```

Regenerate if needed:
```bash
make certs-generate --force
```

### "Port already in use"
Check if something is using LDAP ports:
```bash
lsof -i :389
lsof -i :636
```

### Still stuck?
Check the full troubleshooting section in `README.md` or view logs:
```bash
make logs
```

## Docker Basics (If You're New)

Since you mentioned being new to Docker, here are the basics:

- **Container**: A lightweight, isolated environment running your LDAP server
- **Image**: The blueprint for creating containers (we use `osixia/openldap`)
- **Volume**: Persistent storage for LDAP data (survives restarts)
- **docker-compose**: Tool for managing multi-container applications (LDAP + Admin UI)

When you run `make start`, Docker:
1. Downloads the LDAP image (first time only)
2. Creates containers from the image
3. Mounts your certificates and data files
4. Starts the LDAP service

The `Makefile` is just a collection of shortcuts for common Docker commands.

## Building Elsewhere

This project works on:
- ✅ **MacOS** (with Rancher Desktop or Docker Desktop)
- ✅ **Linux** (with Docker installed)
- ✅ **Windows** (with Docker Desktop + WSL2)

The same `docker-compose.yml` works everywhere - that's the beauty of Docker!

To share your setup with a colleague:
```bash
# Just copy the whole project
git clone <your-repo>
cd ldap_docker
make dev-setup
```

## Quick Reference Card

Keep these handy:

```bash
# Start server
make start

# View logs
make logs

# List users
make test-users

# Stop server
make stop

# Help
make help
```

## Support & Documentation

- **Quick commands**: `make help`
- **Full guide**: `README.md`
- **Examples**: `examples/README.md`
- **Command reference**: `QUICKREF.md`

---

**Ready to start?** Run `./quickstart.sh` or `make dev-setup` and you'll be up in 5 minutes! 🚀

If you run into any issues, check the logs with `make logs` or see the Troubleshooting section in `README.md`.