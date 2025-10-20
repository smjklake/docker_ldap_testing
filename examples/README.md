# LDAP Docker Examples

This directory contains example scripts and applications demonstrating how to use the LDAP server for authentication and user management.

> **📝 Note:** In the examples below, values shown as `{.env:VARIABLE_NAME}` are configurable via environment variables in your `.env` file. The actual default values are: `LDAP_PORT=389`, `LDAPS_PORT=636`, `LDAP_BASE_DN=dc=testing,dc=local`, and `LDAP_ADMIN_PASSWORD=admin_password`. See the main [Configuration](../README.md#configuration) section for all available options.

## Available Examples

### 1. Simple Authentication (`simple_auth.py`)

A Python script demonstrating basic LDAP authentication and user information retrieval.

**Features:**

- Authenticate users with username/password
- Retrieve detailed user information
- Get user group memberships
- List all users in the directory

**Usage:**

```bash
# Authenticate a user (default: jdoe)
python examples/simple_auth.py

# Authenticate with custom credentials
python examples/simple_auth.py --username jsmith --password password123

# List all users
python examples/simple_auth.py --list-users

# Use a different LDAP server
python examples/simple_auth.py --server ldaps://localhost:{.env:LDAPS_PORT}
```

**Example Output:**

```
LDAP Authentication Example
Server: ldap://localhost:{.env:LDAP_PORT}

Attempting to authenticate user: jdoe
✅ Authentication successful for user: jdoe
✅ Authentication successful!

Fetching user information...

==================================================
USER INFORMATION
==================================================
Username:    jdoe
Full Name:   John Doe
First Name:  John
Last Name:   Doe
Email:       jdoe@testing.local
UID Number:  10001
GID Number:  10001
DN:          uid=jdoe,ou=people,{.env:LDAP_BASE_DN}
==================================================

Fetching user groups...
User belongs to 2 group(s):
  • developers
  • users
```

## Using in Your Application

### Python with ldap3

```python
from ldap3 import Server, Connection

# Connect and authenticate
server = Server('ldap://localhost:{.env:LDAP_PORT}')
conn = Connection(
    server,
    user='uid=jdoe,ou=people,{.env:LDAP_BASE_DN}',
    password='password123',
    auto_bind=True
)

# Search for users
conn.search(
    '{.env:LDAP_BASE_DN}',
    '(objectClass=inetOrgPerson)',
    attributes=['uid', 'cn', 'mail']
)

for entry in conn.entries:
    print(f"{entry.cn}: {entry.mail}")

conn.unbind()
```

### Using ldapsearch (Command Line)

```bash
# Search for a user
ldapsearch -H ldap://localhost:{.env:LDAP_PORT} \
  -D "cn=admin,{.env:LDAP_BASE_DN}" \
  -w {.env:LDAP_ADMIN_PASSWORD} \
  -b "{.env:LDAP_BASE_DN}" \
  "(uid=jdoe)"

# List all users
ldapsearch -H ldap://localhost:{.env:LDAP_PORT} \
  -D "cn=admin,{.env:LDAP_BASE_DN}" \
  -w {.env:LDAP_ADMIN_PASSWORD} \
  -b "ou=people,{.env:LDAP_BASE_DN}" \
  "(objectClass=inetOrgPerson)" \
  uid cn mail
```
