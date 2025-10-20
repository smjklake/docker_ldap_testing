#!/usr/bin/env python3
"""
Simple LDAP Authentication Example

This script demonstrates how to authenticate users against the LDAP server
and retrieve user information.

Usage:
    python examples/simple_auth.py
    python examples/simple_auth.py --username jdoe --password password123
"""

import argparse
import os
import sys

try:
    from ldap3 import ALL, Connection, Server
    from ldap3.core.exceptions import LDAPBindError, LDAPException
except ImportError:
    print("Error: ldap3 library not found.")
    print("Install it with: uv pip install ldap3")
    sys.exit(1)


# Configuration
LDAP_PORT = os.environ.get("LDAP_PORT", "389")
LDAP_SERVER = f"ldap://localhost:{LDAP_PORT}"
LDAP_BASE_DN = os.environ.get("LDAP_BASE_DN", "dc=testing,dc=local")
LDAP_PEOPLE_OU = f"ou=people,{LDAP_BASE_DN}"
LDAP_GROUPS_OU = f"ou=groups,{LDAP_BASE_DN}"


class LDAPAuthenticator:
    """Simple LDAP authentication helper."""

    def __init__(self, server_url: str = LDAP_SERVER, base_dn: str = LDAP_BASE_DN):
        """Initialize the authenticator."""
        self.server_url = server_url
        self.base_dn = base_dn
        self.server = Server(server_url, get_info=ALL)

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate a user with their username and password.

        Args:
            username: The user's uid (e.g., 'jdoe')
            password: The user's password

        Returns:
            True if authentication successful, False otherwise
        """
        # Construct the user's DN
        user_dn = f"uid={username},{LDAP_PEOPLE_OU}"

        try:
            # Try to bind with the user's credentials
            conn = Connection(self.server, user=user_dn, password=password)
            if conn.bind():
                print(f"✅ Authentication successful for user: {username}")
                conn.unbind()
                return True
            else:
                print(f"❌ Authentication failed for user: {username}")
                return False

        except LDAPBindError:
            print("❌ Authentication failed: Invalid credentials")
            return False
        except LDAPException as e:
            print(f"❌ LDAP error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def get_user_info(self, username: str, admin_dn: str, admin_password: str) -> dict | None:
        """
        Retrieve detailed information about a user.

        Args:
            username: The user's uid
            admin_dn: Admin DN for searching
            admin_password: Admin password

        Returns:
            Dictionary with user information or None if not found
        """
        try:
            conn = Connection(self.server, user=admin_dn, password=admin_password, auto_bind=True)

            # Search for the user
            conn.search(
                search_base=LDAP_PEOPLE_OU,
                search_filter=f"(uid={username})",
                attributes=["uid", "cn", "sn", "givenName", "mail", "uidNumber", "gidNumber"],
            )

            if conn.entries:
                entry = conn.entries[0]
                user_info = {
                    "username": str(entry.uid),
                    "full_name": str(entry.cn),
                    "first_name": str(entry.givenName) if entry.givenName else "",
                    "last_name": str(entry.sn),
                    "email": str(entry.mail),
                    "uid_number": int(str(entry.uidNumber)) if entry.uidNumber else None,
                    "gid_number": int(str(entry.gidNumber)) if entry.gidNumber else None,
                    "dn": entry.entry_dn,
                }
                conn.unbind()
                return user_info
            else:
                print(f"User '{username}' not found")
                conn.unbind()
                return None

        except LDAPException as e:
            print(f"Error retrieving user info: {e}")
            return None

    def get_user_groups(self, username: str, admin_dn: str, admin_password: str) -> list[str]:
        """
        Get all groups that a user belongs to.

        Args:
            username: The user's uid
            admin_dn: Admin DN for searching
            admin_password: Admin password

        Returns:
            List of group names
        """
        try:
            conn = Connection(self.server, user=admin_dn, password=admin_password, auto_bind=True)

            # Get user's full DN first
            user_dn = f"uid={username},{LDAP_PEOPLE_OU}"

            # Search for groups that have this user as a member
            conn.search(
                search_base=LDAP_GROUPS_OU,
                search_filter=f"(member={user_dn})",
                attributes=["cn"],
            )

            groups = [str(entry.cn) for entry in conn.entries]
            conn.unbind()
            return groups

        except LDAPException as e:
            print(f"Error retrieving user groups: {e}")
            return []

    def list_all_users(self, admin_dn: str, admin_password: str) -> list[dict]:
        """
        List all users in the directory.

        Args:
            admin_dn: Admin DN for searching
            admin_password: Admin password

        Returns:
            List of user dictionaries
        """
        try:
            conn = Connection(self.server, user=admin_dn, password=admin_password, auto_bind=True)

            conn.search(
                search_base=LDAP_PEOPLE_OU,
                search_filter="(objectClass=inetOrgPerson)",
                attributes=["uid", "cn", "mail"],
            )

            users = []
            for entry in conn.entries:
                users.append(
                    {
                        "username": str(entry.uid),
                        "full_name": str(entry.cn),
                        "email": str(entry.mail),
                    }
                )

            conn.unbind()
            return users

        except LDAPException as e:
            print(f"Error listing users: {e}")
            return []


def print_user_info(user_info: dict):
    """Pretty print user information."""
    print("\n" + "=" * 50)
    print("USER INFORMATION")
    print("=" * 50)
    print(f"Username:    {user_info['username']}")
    print(f"Full Name:   {user_info['full_name']}")
    print(f"First Name:  {user_info['first_name']}")
    print(f"Last Name:   {user_info['last_name']}")
    print(f"Email:       {user_info['email']}")
    print(f"UID Number:  {user_info['uid_number']}")
    print(f"GID Number:  {user_info['gid_number']}")
    print(f"DN:          {user_info['dn']}")
    print("=" * 50 + "\n")


def main():
    """Main function demonstrating LDAP authentication."""
    parser = argparse.ArgumentParser(description="LDAP Authentication Example")
    parser.add_argument(
        "--username", "-u", default="jdoe", help="Username to authenticate (default: jdoe)"
    )
    parser.add_argument(
        "--password", "-p", default="password123", help="Password (default: password123)"
    )
    parser.add_argument(
        "--server", "-s", default=LDAP_SERVER, help=f"LDAP server URL (default: {LDAP_SERVER})"
    )
    parser.add_argument("--list-users", action="store_true", help="List all users")

    args = parser.parse_args()

    # Admin credentials for retrieving user info
    admin_dn = os.environ.get("LDAP_ADMIN_DN", f"cn=admin,{LDAP_BASE_DN}")
    admin_password = os.environ.get("LDAP_ADMIN_PASSWORD", "admin_password")

    print("\nLDAP Authentication Example")
    print(f"Server: {args.server}\n")

    # Initialize authenticator
    auth = LDAPAuthenticator(server_url=args.server)

    # List all users if requested
    if args.list_users:
        print("📋 Listing all users...")
        users = auth.list_all_users(admin_dn, admin_password)
        if users:
            print(f"\nFound {len(users)} user(s):\n")
            for user in users:
                print(f"  • {user['username']:12s} - {user['full_name']:20s} ({user['email']})")
        else:
            print("No users found")
        print()
        return

    # Authenticate user
    print(f"Attempting to authenticate user: {args.username}")
    if auth.authenticate(args.username, args.password):
        print("✅ Authentication successful!\n")

        # Get detailed user information
        print("Fetching user information...")
        user_info = auth.get_user_info(args.username, admin_dn, admin_password)
        if user_info:
            print_user_info(user_info)

        # Get user's groups
        print("Fetching user groups...")
        groups = auth.get_user_groups(args.username, admin_dn, admin_password)
        if groups:
            print(f"User belongs to {len(groups)} group(s):")
            for group in groups:
                print(f"  • {group}")
        else:
            print("User is not a member of any groups")
        print()

    else:
        print("❌ Authentication failed!")
        print("\nAvailable test users:")
        print("  • jdoe (password: password123)")
        print("  • jsmith (password: password123)")
        print("  • testuser (password: password123)")
        print("  • admin (password: password123)")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
