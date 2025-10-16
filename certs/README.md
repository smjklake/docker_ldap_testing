# SSL/TLS Certificates for LDAP

This directory should contain your SSL/TLS certificates for the LDAP server.

## Required Files

The OpenLDAP container expects the following files in this directory:

- `ca.crt` - Certificate Authority certificate (your dev-ca root certificate)
- `server.crt` - Server certificate for ldap.testing.local
- `server.key` - Private key for the server certificate

## Using Your Custom Dev-CA Certificates

If you maintain your own dev-ca (as mentioned), simply copy your certificates here:

```bash
# Copy your dev-ca generated certificates to this directory
cp /path/to/your/dev-ca/certs/ldap-server.crt ./server.crt
cp /path/to/your/dev-ca/private/ldap-server.key ./server.key
cp /path/to/your/dev-ca/ca-cert.pem ./ca.crt
```

**Important Notes:**
- The server certificate should be issued for the hostname `ldap.testing.local`
- The certificate can also include SANs (Subject Alternative Names) like:
  - `DNS:ldap.testing.local`
  - `DNS:localhost`
  - `IP:127.0.0.1`
- Ensure the private key is readable by the container (permissions should be 600 or 644)

## Generating Self-Signed Certificates (Quick Start)

If you don't have your dev-ca handy and want to quickly test, you can generate self-signed certificates:

### Option 1: Using OpenSSL (Manual)

```bash
# Generate CA private key
openssl genrsa -out ca.key 4096

# Generate CA certificate
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/C=US/ST=State/L=City/O=Testing Org/CN=Testing CA"

# Generate server private key
openssl genrsa -out server.key 4096

# Generate server certificate signing request
openssl req -new -key server.key -out server.csr \
  -subj "/C=US/ST=State/L=City/O=Testing Org/CN=ldap.testing.local"

# Create extensions file for SAN
cat > server-ext.cnf <<EOF
subjectAltName = DNS:ldap.testing.local,DNS:localhost,IP:127.0.0.1
extendedKeyUsage = serverAuth,clientAuth
EOF

# Sign the server certificate with the CA
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365 \
  -extfile server-ext.cnf

# Clean up temporary files
rm server.csr ca.key server-ext.cnf ca.srl
```

### Option 2: Using the Provided Script

```bash
# Run the certificate generation script from the project root
python scripts/generate_certs.py
```

## File Permissions

Ensure proper permissions for security:

```bash
chmod 644 ca.crt
chmod 644 server.crt
chmod 600 server.key
```

## Verifying Your Certificates

After placing your certificates, verify them:

```bash
# Check certificate details
openssl x509 -in server.crt -text -noout

# Verify certificate chain
openssl verify -CAfile ca.crt server.crt

# Check certificate and key match
openssl x509 -noout -modulus -in server.crt | openssl md5
openssl rsa -noout -modulus -in server.key | openssl md5
# The MD5 hashes should match
```

## Testing LDAPS Connection

Once the container is running with your certificates:

```bash
# Test LDAPS connection (port 636)
openssl s_client -connect localhost:636 -CAfile certs/ca.crt

# Test with ldapsearch
ldapsearch -H ldaps://localhost:636 -x -b "dc=testing,dc=local" \
  -D "cn=admin,dc=testing,dc=local" -w admin_password
```

## Troubleshooting

### Certificate Errors

If you see TLS/SSL errors in the logs:
1. Verify the certificate hostname matches `ldap.testing.local`
2. Check that all three files are present and readable
3. Ensure the server certificate is signed by the CA
4. Check certificate expiration dates

### Container Won't Start

If the container fails to start:
1. Check Docker logs: `docker-compose logs openldap`
2. Verify file permissions on certificate files
3. Ensure certificates are in PEM format (not DER or other formats)

## Security Note

These certificates are for **development use only**. Never use self-signed or development certificates in production environments.