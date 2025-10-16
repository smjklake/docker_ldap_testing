# LDAP Docker Examples

This directory contains example scripts and applications demonstrating how to use the LDAP server for authentication and user management.

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
python examples/simple_auth.py --server ldaps://localhost:636
```

**Example Output:**

```
🔐 LDAP Authentication Example
Server: ldap://localhost:389

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
DN:          uid=jdoe,ou=people,dc=testing,dc=local
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
server = Server('ldap://localhost:389')
conn = Connection(
    server,
    user='uid=jdoe,ou=people,dc=testing,dc=local',
    password='password123',
    auto_bind=True
)

# Search for users
conn.search(
    'dc=testing,dc=local',
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
ldapsearch -H ldap://localhost:389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "dc=testing,dc=local" \
  "(uid=jdoe)"

# List all users
ldapsearch -H ldap://localhost:389 \
  -D "cn=admin,dc=testing,dc=local" \
  -w admin_password \
  -b "ou=people,dc=testing,dc=local" \
  "(objectClass=inetOrgPerson)" \
  uid cn mail
```

### Web Application Integration

#### Flask Example

```python
from flask import Flask, request, jsonify
from ldap3 import Server, Connection

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    server = Server('ldap://localhost:389')
    user_dn = f'uid={username},ou=people,dc=testing,dc=local'
    
    try:
        conn = Connection(server, user=user_dn, password=password)
        if conn.bind():
            return jsonify({'status': 'success', 'message': 'Authenticated'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    except:
        return jsonify({'status': 'error', 'message': 'Authentication failed'}), 401
```

#### Django Example

```python
# settings.py
import ldap
from django_auth_ldap.config import LDAPSearch

AUTH_LDAP_SERVER_URI = "ldap://localhost:389"
AUTH_LDAP_BIND_DN = "cn=admin,dc=testing,dc=local"
AUTH_LDAP_BIND_PASSWORD = "admin_password"
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=people,dc=testing,dc=local",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"
)

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

## Common Integration Patterns

### 1. Simple Bind Authentication

The most straightforward approach - try to bind with user credentials:

```python
def authenticate_user(username, password):
    server = Server('ldap://localhost:389')
    user_dn = f'uid={username},ou=people,dc=testing,dc=local'
    conn = Connection(server, user=user_dn, password=password)
    return conn.bind()
```

### 2. Search and Bind

Search for the user first, then authenticate:

```python
def authenticate_user(username, password):
    # First, search for the user with admin credentials
    server = Server('ldap://localhost:389')
    admin_conn = Connection(
        server,
        user='cn=admin,dc=testing,dc=local',
        password='admin_password',
        auto_bind=True
    )
    
    admin_conn.search(
        'ou=people,dc=testing,dc=local',
        f'(uid={username})',
        attributes=['dn']
    )
    
    if not admin_conn.entries:
        return False
    
    user_dn = admin_conn.entries[0].entry_dn
    admin_conn.unbind()
    
    # Now authenticate as the user
    user_conn = Connection(server, user=user_dn, password=password)
    return user_conn.bind()
```

### 3. Group-Based Authorization

Check if user belongs to specific groups:

```python
def user_has_role(username, required_group):
    server = Server('ldap://localhost:389')
    conn = Connection(
        server,
        user='cn=admin,dc=testing,dc=local',
        password='admin_password',
        auto_bind=True
    )
    
    user_dn = f'uid={username},ou=people,dc=testing,dc=local'
    
    conn.search(
        'ou=groups,dc=testing,dc=local',
        f'(&(objectClass=groupOfNames)(member={user_dn})(cn={required_group}))',
        attributes=['cn']
    )
    
    return len(conn.entries) > 0
```

## Testing Your Integration

### 1. Start the LDAP Server

```bash
make start
```

### 2. Test Connection

```bash
python examples/simple_auth.py --list-users
```

### 3. Test Authentication

```bash
python examples/simple_auth.py --username jdoe --password password123
```

### 4. Test with Your Application

Point your application to:
- LDAP URL: `ldap://localhost:389`
- LDAPS URL: `ldaps://localhost:636` (with SSL)
- Base DN: `dc=testing,dc=local`

## Available Test Accounts

| Username | Password | Groups | Purpose |
|----------|----------|--------|---------|
| admin | password123 | admins | Administrative testing |
| jdoe | password123 | developers, users | Regular user testing |
| jsmith | password123 | developers, users | Regular user testing |
| testuser | password123 | users | Basic user testing |

## SSL/TLS Configuration

For production-like testing with LDAPS:

```python
import ssl
from ldap3 import Server, Connection, Tls

tls = Tls(
    ca_certs_file='certs/ca.crt',
    validate=ssl.CERT_REQUIRED
)

server = Server('ldaps://localhost:636', use_ssl=True, tls=tls)
conn = Connection(server, user=user_dn, password=password, auto_bind=True)
```

## Troubleshooting

### Connection Refused

```bash
# Check if LDAP server is running
make status

# Start if not running
make start
```

### Authentication Fails

```bash
# Verify user exists
make test-users

# Check LDAP logs
make logs
```

### Python ImportError

```bash
# Install ldap3 library
uv pip install ldap3
# or
pip install ldap3
```

## Additional Resources

- [ldap3 Documentation](https://ldap3.readthedocs.io/)
- [LDAP Protocol Overview](https://ldap.com/ldap-protocol/)
- [Django LDAP Authentication](https://django-auth-ldap.readthedocs.io/)
- [Flask-LDAP3-Login](https://flask-ldap3-login.readthedocs.io/)

## Contributing Examples

Have an example for a specific framework or use case? Contributions are welcome!

Examples we'd love to see:
- Express.js / Node.js authentication
- Ruby on Rails integration
- Go LDAP client
- Java Spring Security LDAP
- PHP authentication
- Docker Compose with application stack

Submit a pull request with your example!