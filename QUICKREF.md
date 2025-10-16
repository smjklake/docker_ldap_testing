# LDAP Docker Quick Reference

Quick reference for common operations and configurations.

## 🚀 Quick Start

```bash
# Complete setup
make dev-setup

# Or step by step
make install              # Install dependencies
make certs-generate       # Generate certificates
make start                # Start server
make test-connection      # Test it works
```

## 🎯 Common Commands

### Server Management

```bash
make start                # Start LDAP server
make stop                 # Stop LDAP server
make restart              # Restart LDAP server
make down                 # Stop and remove containers
make logs                 # View logs (follow mode)
make status               # Check container status
```

### Testing

```bash
make test-connection      # Test LDAP connection
make test-auth            # Test authentication
make test-users           # List all users
make test-all             # Run all tests
```

### Certificates

```bash
make certs-generate       # Generate self-signed certs
make certs-check          # Verify certificates
```

## 🔑 Default Credentials

### Admin Access

- **DN:** `cn=admin,dc=testing,dc=local`
- **Password:** `admin_password`
- **Base DN:** `dc=testing,dc=local`

### phpLDAPadmin

- URL: http://localhost:8080
- Login DN: `cn=admin,dc=testing,dc=local`
- Password: `admin_password`

## 👥 Test Users

All users have password: `password123`

| Username | Full Name | Email | DN |
|----------|-----------|-------|-----|
| `admin` | Admin User | admin@testing.local | `uid=admin,ou=people,dc=testing,dc=local` |
| `jdoe` | John Doe | jdoe@testing.local | `uid=jdoe,ou=people,dc=testing,dc=local` |
| `jsmith` | Jane Smith | jsmith@testing.local | `uid=jsmith,ou=people,dc=testing,dc=local` |
| `testuser` | Test User | testuser@testing.local | `uid=testuser,ou=people,dc=testing,dc=local` |

## 🌐 Service Ports

| Service | Port | URL/Connection |
|---------|------|----------------|
| LDAP | 389 | `ldap://localhost:389` |
| LDAPS | 636 | `ldaps://localhost:636` |
| phpLDAPadmin | 8080 | `http://localhost:8080` |

## 🔍 Common LDAP Queries

### Search All Users

```bash
ldapsearch -H ldap://localhost:389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "ou=people,dc=testing,dc=local" \
  "(objectClass=inetOrgPerson)"
```

### Search Specific User

```bash
ldapsearch -H ldap://localhost:389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "dc=testing,dc=local" \
  "(uid=jdoe)"
```

### Search All Groups

```bash
ldapsearch -H ldap://localhost:389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "ou=groups,dc=testing,dc=local" \
  "(objectClass=groupOfNames)"
```

### Anonymous Bind (Read-Only)

```bash
ldapsearch -H ldap://localhost:389 \
  -x \
  -b "dc=testing,dc=local" \
  "(objectClass=*)"
```

## 🔒 LDAPS/SSL Testing

### Test SSL Connection

```bash
openssl s_client -connect localhost:636 -CAfile certs/ca.crt
```

### LDAPS Search

```bash
ldapsearch -H ldaps://localhost:636 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "dc=testing,dc=local"
```

### Verify Certificate

```bash
openssl verify -CAfile certs/ca.crt certs/server.crt
openssl x509 -in certs/server.crt -text -noout
```

## 🐍 Python LDAP3 Examples

### Simple Connection

```python
from ldap3 import Server, Connection

server = Server('ldap://localhost:389')
conn = Connection(server, 
                  user='cn=admin,dc=testing,dc=local',
                  password='admin_password',
                  auto_bind=True)
print("Connected!")
conn.unbind()
```

### Search Users

```python
from ldap3 import Server, Connection

server = Server('ldap://localhost:389')
conn = Connection(server, 
                  user='cn=admin,dc=testing,dc=local',
                  password='admin_password',
                  auto_bind=True)

conn.search('dc=testing,dc=local',
            '(objectClass=inetOrgPerson)',
            attributes=['uid', 'cn', 'mail'])

for entry in conn.entries:
    print(f"{entry.cn}: {entry.mail}")

conn.unbind()
```

### Authenticate User

```python
from ldap3 import Server, Connection

server = Server('ldap://localhost:389')
conn = Connection(server,
                  user='uid=jdoe,ou=people,dc=testing,dc=local',
                  password='password123')

if conn.bind():
    print("Authentication successful!")
else:
    print("Authentication failed!")
conn.unbind()
```

## 🐳 Docker Commands

### View Logs

```bash
docker-compose logs -f openldap        # Follow LDAP logs
docker-compose logs --tail=100 openldap  # Last 100 lines
docker-compose logs phpldapadmin       # Admin UI logs
```

### Container Shell Access

```bash
docker-compose exec openldap bash      # Shell in LDAP container
docker ps                              # List running containers
docker-compose ps                      # List project containers
```

### Volume Management

```bash
docker volume ls                       # List volumes
docker-compose down -v                 # Remove volumes (deletes data!)
```

## 🔧 Troubleshooting Quick Fixes

### Server Won't Start

```bash
# Check if ports are in use
lsof -i :389
lsof -i :636
lsof -i :8080

# Check Docker is running
docker version

# View error logs
docker-compose logs openldap
```

### Certificate Errors

```bash
# Verify certificates exist
ls -la certs/

# Regenerate certificates
make certs-generate --force

# Check certificate validity
openssl x509 -in certs/server.crt -noout -dates
```

### Connection Refused

```bash
# Check container is running
docker-compose ps

# Wait for initialization (can take 10-30 seconds)
make logs

# Restart server
make restart
```

### Authentication Fails

```bash
# Verify credentials
# Default: cn=admin,dc=testing,dc=local / admin_password

# Check if users are loaded
make test-users

# View LDAP directory structure
ldapsearch -H ldap://localhost:389 -x -b "dc=testing,dc=local" -s base
```

### Data Not Appearing

```bash
# Check if LDIF files were loaded
docker-compose logs openldap | grep -i ldif

# Rebuild with fresh data
make down-volumes  # WARNING: Deletes all data!
make start
```

## 📁 File Locations

### Configuration Files

- `docker-compose.yml` - Docker services configuration
- `pyproject.toml` - Python dependencies
- `.env.example` - Environment variables template

### Data Files

- `ldif/01-users.ldif` - Initial LDAP data
- `certs/` - SSL certificates (git-ignored)

### Scripts

- `scripts/cli.py` - CLI management tool
- `scripts/generate_certs.py` - Certificate generator
- `quickstart.sh` - Interactive setup script

## 🎓 LDAP Basics

### DN (Distinguished Name)

Format: `attribute=value,ou=unit,dc=domain,dc=tld`

Examples:
- `cn=admin,dc=testing,dc=local` - Admin user
- `uid=jdoe,ou=people,dc=testing,dc=local` - Regular user
- `cn=developers,ou=groups,dc=testing,dc=local` - Group

### Common Object Classes

- `inetOrgPerson` - Person with internet attributes
- `posixAccount` - Unix/Linux account
- `groupOfNames` - Group with members

### Common Attributes

- `uid` - User ID (username)
- `cn` - Common Name (full name)
- `sn` - Surname (last name)
- `mail` - Email address
- `userPassword` - Hashed password
- `member` - Group member DN

## 🔗 Useful Links

- [OpenLDAP Documentation](https://www.openldap.org/doc/)
- [LDAP3 Python Library](https://ldap3.readthedocs.io/)
- [RFC 4511 - LDAP Protocol](https://tools.ietf.org/html/rfc4511)
- [phpLDAPadmin](http://phpldapadmin.sourceforge.net/)

## 💡 Tips

1. **Use LDAPS in applications**: Always prefer `ldaps://` over `ldap://`
2. **Test with anonymous bind first**: Use `-x` flag with ldapsearch
3. **Check logs when troubleshooting**: `make logs` is your friend
4. **Certificate hostname must match**: Ensure SAN includes `ldap.testing.local`
5. **Wait after starting**: Server needs 10-30 seconds to initialize
6. **Backup before experimenting**: Use `make down` not `make down-volumes`

---

**Need more help?** See full documentation in README.md