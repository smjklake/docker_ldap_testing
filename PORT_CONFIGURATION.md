# Port Configuration Guide

This guide explains how to configure custom ports for your LDAP Docker environment to avoid conflicts with other services.

## Quick Start

**To change ports, simply edit the `.env` file:**

```bash
# Edit .env file
LDAP_PORT=20389
LDAPS_PORT=20636
PHPLDAPADMIN_PORT=8080
```

Then restart:
```bash
make down && make start
```

That's it! All scripts and tools will automatically use your custom ports.

---

## Why Custom Ports?

You might want to use custom ports if:
- You have another LDAP server running on standard ports (389/636)
- Port 389 requires root/admin privileges
- You're running multiple LDAP environments simultaneously
- Your organization has specific port requirements

## Files Involved

The port configuration system uses these files:

### 1. `.env` - Your Configuration (Edit This!)
```bash
LDAP_PORT=20389          # Your custom LDAP port
LDAPS_PORT=20636         # Your custom LDAPS port
PHPLDAPADMIN_PORT=8080   # Web admin interface port
```

### 2. `docker-compose.yml` - Uses Environment Variables
```yaml
ports:
  - "${LDAP_PORT:-389}:389"      # Host:Container mapping
  - "${LDAPS_PORT:-636}:636"
```

The `${LDAP_PORT:-389}` syntax means:
- Use `$LDAP_PORT` if set in `.env`
- Otherwise use default `389`

### 3. Scripts - Auto-detect Ports
All Python scripts and Makefile commands read from `.env` automatically:
- `scripts/cli.py`
- `scripts/ldapsearch_helper.sh`
- `examples/simple_auth.py`
- `Makefile`

## How to Change Ports

### Method 1: Edit .env File (Recommended)

1. **Edit `.env`:**
   ```bash
   vim .env  # or your favorite editor
   ```

2. **Change the port values:**
   ```bash
   LDAP_PORT=20389
   LDAPS_PORT=20636
   ```

3. **Restart the containers:**
   ```bash
   make down && make start
   ```

4. **Verify:**
   ```bash
   docker-compose ps
   # Should show 0.0.0.0:20389->389/tcp
   ```

### Method 2: Environment Variables (Temporary)

For one-time use without modifying `.env`:

```bash
LDAP_PORT=30389 LDAPS_PORT=30636 docker-compose up -d
```

### Method 3: Create .env.local (Advanced)

For personal overrides without modifying the main `.env`:

```bash
# Create .env.local (git-ignored)
echo "LDAP_PORT=12389" > .env.local
echo "LDAPS_PORT=12636" >> .env.local

# Docker Compose will merge both files
docker-compose up -d
```

## Testing with Custom Ports

### Automatic - Use Our Tools

All our tools automatically detect your ports from `.env`:

```bash
# These all work automatically with your custom ports
make test-users
make test-connection
uv run python examples/simple_auth.py
```

### Generate ldapsearch Commands

Use our helper script to generate commands with your ports:

```bash
./scripts/ldapsearch_helper.sh
```

Output includes commands like:
```bash
# List all users
ldapsearch -H ldap://localhost:20389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "ou=people,dc=testing,dc=local" \
  "(objectClass=inetOrgPerson)" \
  uid cn mail
```

### Manual ldapsearch Commands

Replace `389` with your `LDAP_PORT` and `636` with your `LDAPS_PORT`:

```bash
# Standard LDAP (unencrypted)
ldapsearch -H ldap://localhost:20389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "dc=testing,dc=local"

# LDAPS (SSL/TLS)
ldapsearch -H ldaps://localhost:20636 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "dc=testing,dc=local"

# Search for specific user
ldapsearch -H ldap://localhost:20389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "dc=testing,dc=local" \
  "(uid=jdoe)"

# Test user authentication
ldapsearch -H ldap://localhost:20389 \
  -D "uid=jdoe,ou=people,dc=testing,dc=local" \
  -w password123 \
  -b "dc=testing,dc=local" \
  "(uid=jdoe)"
```

### Using Python

```python
import os
from ldap3 import Server, Connection

# Automatically uses LDAP_PORT from environment
port = os.environ.get('LDAP_PORT', '389')
server = Server(f'ldap://localhost:{port}')
conn = Connection(server, 
                  user='cn=admin,dc=testing,dc=local',
                  password='admin_password',
                  auto_bind=True)

conn.search('dc=testing,dc=local', '(objectClass=*)')
print(f"Connected on port {port}")
conn.unbind()
```

## Common Port Configurations

### Development (Unprivileged Ports)
```bash
LDAP_PORT=20389
LDAPS_PORT=20636
PHPLDAPADMIN_PORT=8080
```

### Testing (High Ports)
```bash
LDAP_PORT=30389
LDAPS_PORT=30636
PHPLDAPADMIN_PORT=8090
```

### Multiple Environments
```bash
# Environment 1 (.env)
LDAP_PORT=20389
LDAPS_PORT=20636

# Environment 2 (separate directory or .env.local)
LDAP_PORT=21389
LDAPS_PORT=21636
```

## Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:20389 failed: port is already allocated`

**Check what's using the port:**
```bash
lsof -i :20389
# or
netstat -an | grep 20389
```

**Solutions:**
1. Stop the conflicting service
2. Choose a different port in `.env`
3. Use `make down` to stop this LDAP server first

### Scripts Not Using Custom Ports

**Problem:** Scripts still connect to port 389

**Solution:** Ensure `.env` is loaded:

1. **Check .env exists:**
   ```bash
   ls -la .env
   ```

2. **Verify ports are set:**
   ```bash
   grep LDAP_PORT .env
   ```

3. **Reload environment:**
   ```bash
   source .env  # For bash scripts
   make down && make start  # Restart containers
   ```

### Docker Compose Not Reading .env

**Problem:** Containers still on default ports

**Check:**
```bash
# View what Docker Compose sees
docker-compose config | grep -A2 ports
```

**Solution:**
```bash
# Ensure .env is in project root
pwd  # Should be ldap_docker/
ls .env  # Should exist

# Force reload
docker-compose down
docker-compose up -d
```

### Can't Connect After Port Change

**Verify containers are running on correct ports:**
```bash
docker-compose ps
# Should show: 0.0.0.0:20389->389/tcp
```

**Test connectivity:**
```bash
# Test if port is listening
nc -zv localhost 20389

# Test LDAP response
ldapsearch -H ldap://localhost:20389 -x -b "" -s base
```

**Check logs:**
```bash
make logs
# Look for: "slapd starting"
```

## Port Reference Table

| Service | Default Port | Docker Internal Port | Configurable Via |
|---------|--------------|---------------------|------------------|
| LDAP | 389 | 389 | `LDAP_PORT` in .env |
| LDAPS | 636 | 636 | `LDAPS_PORT` in .env |
| phpLDAPadmin | 8080 | 80 | `PHPLDAPADMIN_PORT` in .env |

**Note:** The "Docker Internal Port" (right side of mapping) never changes. Only the host port (left side) is configurable.

## Advanced: Port Mapping Explained

Docker port mapping format: `HOST:CONTAINER`

```yaml
ports:
  - "20389:389"
```

This means:
- **20389** = Port on your Mac (accessible via `localhost:20389`)
- **389** = Port inside the Docker container (LDAP's standard port)

The container always listens on 389 internally. We just map it to 20389 externally.

## Testing Multiple Configurations

Run multiple LDAP servers simultaneously:

```bash
# Terminal 1: First instance
cd ldap_docker_1
echo "LDAP_PORT=20389" > .env
echo "LDAPS_PORT=20636" >> .env
make start

# Terminal 2: Second instance
cd ldap_docker_2
echo "LDAP_PORT=21389" > .env
echo "LDAPS_PORT=21636" >> .env
make start

# Now you have two LDAP servers running!
ldapsearch -H ldap://localhost:20389 ...  # Server 1
ldapsearch -H ldap://localhost:21389 ...  # Server 2
```

## Best Practices

1. **Use .env for configuration** - Don't hardcode ports in scripts
2. **Document your ports** - Add comments in .env explaining your choices
3. **Use unprivileged ports** - Ports above 1024 don't require root
4. **Avoid common ports** - Skip 8080, 3000, 5000 (often used by other tools)
5. **Be consistent** - If LDAP is 20389, make LDAPS 20636 (same prefix)

## Integration Examples

### Configure Your Application

After changing ports, update your application's LDAP configuration:

```python
# Django settings.py
AUTH_LDAP_SERVER_URI = "ldap://localhost:20389"

# Flask
LDAP_HOST = "localhost"
LDAP_PORT = 20389

# Environment variable
export LDAP_URL="ldap://localhost:20389"
```

### Using with Docker Networks

If your application is also in Docker:

```yaml
# Your app's docker-compose.yml
services:
  your-app:
    environment:
      LDAP_URL: "ldap://ldap-server:389"  # Use container name and internal port
    networks:
      - ldap_docker_ldap-network  # Connect to LDAP network

networks:
  ldap_docker_ldap-network:
    external: true
```

## Quick Reference

```bash
# View current configuration
cat .env | grep PORT

# Generate ldapsearch commands
./scripts/ldapsearch_helper.sh

# Test connection on custom port
make test-connection

# Check what ports containers are using
docker-compose ps

# Change ports (example)
echo "LDAP_PORT=12389" > .env
echo "LDAPS_PORT=12636" >> .env
make down && make start

# Verify new ports work
make test-users
```

## Summary

**To use custom ports:**
1. Edit `LDAP_PORT` and `LDAPS_PORT` in `.env`
2. Run `make down && make start`
3. All tools automatically use your new ports!

**Need ldapsearch commands?**
- Run `./scripts/ldapsearch_helper.sh`
- Or manually replace 389 → your LDAP_PORT, 636 → your LDAPS_PORT

That's it! The port configuration system is designed to be simple and automatic.

---

**See Also:**
- [README.md](README.md) - Full documentation
- [GETTING_STARTED.md](GETTING_STARTED.md) - Setup guide
- [QUICKREF.md](QUICKREF.md) - Command reference