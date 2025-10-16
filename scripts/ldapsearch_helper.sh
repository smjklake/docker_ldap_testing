#!/usr/bin/env bash
#
# LDAP Search Helper
# Generates ldapsearch commands configured for your environment
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# Set defaults if not in environment
LDAP_PORT=${LDAP_PORT:-389}
LDAPS_PORT=${LDAPS_PORT:-636}
LDAP_BASE_DN=${LDAP_BASE_DN:-dc=testing,dc=local}
LDAP_ADMIN_PASSWORD=${LDAP_ADMIN_PASSWORD:-admin_password}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}LDAP Search Command Generator${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Configuration:"
echo "  LDAP Port:  $LDAP_PORT"
echo "  LDAPS Port: $LDAPS_PORT"
echo "  Base DN:    $LDAP_BASE_DN"
echo ""

# Function to print a command example
print_cmd() {
    local description="$1"
    local command="$2"

    echo -e "${GREEN}# $description${NC}"
    echo -e "${YELLOW}$command${NC}"
    echo ""
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Basic Connection Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

print_cmd "Test server is responding (anonymous bind)" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -x -b \"\" -s base"

print_cmd "Test with admin credentials" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"$LDAP_BASE_DN\""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Search Users${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

print_cmd "List all users" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=people,$LDAP_BASE_DN\" \"(objectClass=inetOrgPerson)\" uid cn mail"

print_cmd "Search for specific user (jdoe)" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"$LDAP_BASE_DN\" \"(uid=jdoe)\""

print_cmd "Test user authentication (as jdoe)" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"uid=jdoe,ou=people,$LDAP_BASE_DN\" -w password123 -b \"$LDAP_BASE_DN\" \"(uid=jdoe)\""

print_cmd "Get all user attributes for jdoe" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=people,$LDAP_BASE_DN\" \"(uid=jdoe)\" '*' '+'"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Search Groups${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

print_cmd "List all groups" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=groups,$LDAP_BASE_DN\" \"(objectClass=groupOfNames)\" cn member"

print_cmd "Find groups for user jdoe" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=groups,$LDAP_BASE_DN\" \"(member=uid=jdoe,ou=people,$LDAP_BASE_DN)\" cn"

print_cmd "Get members of developers group" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=groups,$LDAP_BASE_DN\" \"(cn=developers)\" member"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}LDAPS (SSL/TLS) Commands${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

print_cmd "Test LDAPS connection" \
"ldapsearch -H ldaps://localhost:$LDAPS_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"$LDAP_BASE_DN\""

print_cmd "LDAPS with CA certificate verification" \
"LDAPTLS_CACERT=$PROJECT_ROOT/certs/ca.crt ldapsearch -H ldaps://localhost:$LDAPS_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"$LDAP_BASE_DN\""

print_cmd "Check SSL certificate" \
"openssl s_client -connect localhost:$LDAPS_PORT -CAfile $PROJECT_ROOT/certs/ca.crt -showcerts"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Secure Commands (Password Prompt)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

print_cmd "Admin search with password prompt (more secure)" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -W -b \"$LDAP_BASE_DN\""

print_cmd "User authentication with password prompt" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"uid=jdoe,ou=people,$LDAP_BASE_DN\" -W -b \"$LDAP_BASE_DN\" \"(uid=jdoe)\""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Advanced Queries${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

print_cmd "Search with wildcard (all users starting with 'j')" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=people,$LDAP_BASE_DN\" \"(uid=j*)\" uid cn"

print_cmd "Search by email domain" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=people,$LDAP_BASE_DN\" \"(mail=*@testing.local)\" uid mail"

print_cmd "Count total users" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"ou=people,$LDAP_BASE_DN\" \"(objectClass=inetOrgPerson)\" dn | grep -c '^dn:'"

print_cmd "Export entire directory to LDIF file" \
"ldapsearch -H ldap://localhost:$LDAP_PORT -D \"cn=admin,$LDAP_BASE_DN\" -w $LDAP_ADMIN_PASSWORD -b \"$LDAP_BASE_DN\" -LLL > ldap_backup.ldif"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Quick Reference${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Common flags:"
echo "  -H  : LDAP URI (ldap:// or ldaps://)"
echo "  -D  : Bind DN (user to authenticate as)"
echo "  -w  : Password (visible in process list)"
echo "  -W  : Prompt for password (more secure)"
echo "  -x  : Use simple authentication"
echo "  -b  : Base DN to search from"
echo "  -s  : Scope (base, one, sub)"
echo "  -LLL: LDIF output without comments"
echo ""
echo "Test credentials:"
echo "  Admin:    cn=admin,$LDAP_BASE_DN / $LDAP_ADMIN_PASSWORD"
echo "  Test user: uid=jdoe,ou=people,$LDAP_BASE_DN / password123"
echo ""
echo -e "${GREEN}Tip:${NC} Copy any command above and run it in your terminal!"
echo ""

# Option to run a command interactively
if [ "$1" = "--interactive" ] || [ "$1" = "-i" ]; then
    echo ""
    echo "Select a command to run:"
    echo "  1) List all users"
    echo "  2) Search for user jdoe"
    echo "  3) Test user authentication"
    echo "  4) List all groups"
    echo "  5) Test LDAPS connection"
    echo "  6) Custom command"
    echo ""
    read -p "Choice (1-6): " choice

    case $choice in
        1)
            ldapsearch -H ldap://localhost:$LDAP_PORT -D "cn=admin,$LDAP_BASE_DN" -w $LDAP_ADMIN_PASSWORD -b "ou=people,$LDAP_BASE_DN" "(objectClass=inetOrgPerson)" uid cn mail
            ;;
        2)
            ldapsearch -H ldap://localhost:$LDAP_PORT -D "cn=admin,$LDAP_BASE_DN" -w $LDAP_ADMIN_PASSWORD -b "$LDAP_BASE_DN" "(uid=jdoe)"
            ;;
        3)
            read -p "Enter password for jdoe: " -s user_pass
            echo ""
            ldapsearch -H ldap://localhost:$LDAP_PORT -D "uid=jdoe,ou=people,$LDAP_BASE_DN" -w "$user_pass" -b "$LDAP_BASE_DN" "(uid=jdoe)"
            ;;
        4)
            ldapsearch -H ldap://localhost:$LDAP_PORT -D "cn=admin,$LDAP_BASE_DN" -w $LDAP_ADMIN_PASSWORD -b "ou=groups,$LDAP_BASE_DN" "(objectClass=groupOfNames)" cn member
            ;;
        5)
            LDAPTLS_CACERT=$PROJECT_ROOT/certs/ca.crt ldapsearch -H ldaps://localhost:$LDAPS_PORT -D "cn=admin,$LDAP_BASE_DN" -w $LDAP_ADMIN_PASSWORD -b "$LDAP_BASE_DN"
            ;;
        6)
            read -p "Enter custom filter: " filter
            ldapsearch -H ldap://localhost:$LDAP_PORT -D "cn=admin,$LDAP_BASE_DN" -w $LDAP_ADMIN_PASSWORD -b "$LDAP_BASE_DN" "$filter"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
fi
