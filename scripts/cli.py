#!/usr/bin/env python3
"""
CLI tool for managing the LDAP Docker development environment.

This tool provides convenient commands for starting, stopping, and testing
the LDAP server, as well as managing test users and certificates.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import click

try:
    import ldap3
    from ldap3 import ALL, Connection, Server
    from ldap3.core.exceptions import LDAPException
except ImportError:
    ldap3 = None


# Constants
PROJECT_ROOT = Path(__file__).parent.parent
CERTS_DIR = PROJECT_ROOT / "certs"
LDIF_DIR = PROJECT_ROOT / "ldif"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = int(os.environ.get("LDAP_PORT", "389"))
DEFAULT_LDAPS_PORT = int(os.environ.get("LDAPS_PORT", "636"))
DEFAULT_BASE_DN = "dc=testing,dc=local"
DEFAULT_ADMIN_DN = "cn=admin,dc=testing,dc=local"
DEFAULT_ADMIN_PASSWORD = "admin_password"


def run_command(cmd: list[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    if cwd is None:
        cwd = PROJECT_ROOT

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running command: {' '.join(cmd)}", err=True)
        click.echo(f"Exit code: {e.returncode}", err=True)
        if e.stdout:
            click.echo(f"stdout: {e.stdout}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        raise


def check_docker():
    """Check if Docker is available."""
    try:
        result = run_command(["docker", "version"], check=False)
        if result.returncode != 0:
            click.echo("Error: Docker is not running or not installed.", err=True)
            click.echo("Please ensure Docker (or Rancher Desktop) is running.", err=True)
            sys.exit(1)
    except FileNotFoundError:
        click.echo("Error: Docker command not found.", err=True)
        click.echo("Please install Docker or Rancher Desktop.", err=True)
        sys.exit(1)


def check_certificates():
    """Check if SSL certificates exist."""
    required_files = ["ca.crt", "server.crt", "server.key"]
    missing = [f for f in required_files if not (CERTS_DIR / f).exists()]

    if missing:
        click.echo("⚠️  Warning: Missing SSL certificate files:", err=True)
        for f in missing:
            click.echo(f"  - {CERTS_DIR / f}", err=True)
        click.echo("\nYou can:", err=True)
        click.echo("  1. Copy your dev-ca certificates to the certs/ directory", err=True)
        click.echo("  2. Generate self-signed certificates: ldap-docker certs generate", err=True)
        return False
    return True


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """LDAP Docker Development Tool - Manage your OpenLDAP development environment."""
    pass


@cli.group()
def server():
    """Manage the LDAP server container."""
    pass


@server.command("start")
@click.option("--detach", "-d", is_flag=True, default=True, help="Run in detached mode")
@click.option("--build", is_flag=True, help="Build images before starting")
def server_start(detach: bool, build: bool):
    """Start the LDAP server and optional phpLDAPadmin."""
    check_docker()
    check_certificates()

    cmd = ["docker-compose", "up"]
    if detach:
        cmd.append("-d")
    if build:
        cmd.append("--build")

    click.echo("Starting LDAP server...")
    result = run_command(cmd)

    if result.returncode == 0:
        click.echo("✅ LDAP server started successfully!")
        click.echo(f"\nLDAP server is available at:")
        click.echo(f"  - LDAP:  ldap://localhost:389")
        click.echo(f"  - LDAPS: ldaps://localhost:636")
        click.echo(f"  - Admin: http://localhost:8080 (phpLDAPadmin)")
        click.echo(f"\nAdmin credentials:")
        click.echo(f"  - DN: {DEFAULT_ADMIN_DN}")
        click.echo(f"  - Password: {DEFAULT_ADMIN_PASSWORD}")

        if detach:
            click.echo("\nWaiting for server to be ready...")
            time.sleep(5)
            # Try to check if server is responding
            result = run_command(
                ["docker-compose", "ps", "--filter", "status=running"],
                check=False
            )
            if "ldap-server" in result.stdout:
                click.echo("✅ Server is running")


@server.command("stop")
def server_stop():
    """Stop the LDAP server."""
    check_docker()

    click.echo("Stopping LDAP server...")
    run_command(["docker-compose", "stop"])
    click.echo("✅ LDAP server stopped")


@server.command("restart")
def server_restart():
    """Restart the LDAP server."""
    check_docker()

    click.echo("Restarting LDAP server...")
    run_command(["docker-compose", "restart"])
    click.echo("✅ LDAP server restarted")

    click.echo("\nWaiting for server to be ready...")
    time.sleep(5)


@server.command("down")
@click.option("--volumes", "-v", is_flag=True, help="Remove volumes (deletes all data)")
def server_down(volumes: bool):
    """Stop and remove the LDAP server containers."""
    check_docker()

    cmd = ["docker-compose", "down"]
    if volumes:
        if not click.confirm("⚠️  This will delete all LDAP data. Continue?"):
            click.echo("Aborted.")
            return
        cmd.append("-v")

    click.echo("Removing LDAP server containers...")
    run_command(cmd)
    click.echo("✅ Containers removed")


@server.command("logs")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--tail", "-n", default=100, help="Number of lines to show from the end")
@click.option("--service", default="openldap", help="Service to show logs for")
def server_logs(follow: bool, tail: int, service: str):
    """View LDAP server logs."""
    check_docker()

    cmd = ["docker-compose", "logs", f"--tail={tail}"]
    if follow:
        cmd.append("-f")
    cmd.append(service)

    # For follow mode, we want to pass through to the terminal
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        click.echo("\n")


@server.command("status")
def server_status():
    """Check LDAP server status."""
    check_docker()

    result = run_command(["docker-compose", "ps"], check=False)
    click.echo(result.stdout)


@cli.group()
def certs():
    """Manage SSL/TLS certificates."""
    pass


@certs.command("generate")
@click.option("--force", is_flag=True, help="Overwrite existing certificates")
@click.option("--hostname", default="ldap.testing.local", help="Server hostname")
def certs_generate(force: bool, hostname: str):
    """Generate self-signed SSL certificates for development."""
    script_path = PROJECT_ROOT / "scripts" / "generate_certs.py"

    if not script_path.exists():
        click.echo(f"Error: Certificate generation script not found: {script_path}", err=True)
        sys.exit(1)

    cmd = [sys.executable, str(script_path), "--hostname", hostname]
    if force:
        cmd.append("--force")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        click.echo("Failed to generate certificates", err=True)
        sys.exit(1)


@certs.command("check")
def certs_check():
    """Verify SSL certificates."""
    required_files = {
        "ca.crt": "CA Certificate",
        "server.crt": "Server Certificate",
        "server.key": "Server Private Key",
    }

    click.echo("Checking SSL certificates...\n")

    all_exist = True
    for filename, description in required_files.items():
        filepath = CERTS_DIR / filename
        if filepath.exists():
            size = filepath.stat().st_size
            click.echo(f"✅ {description}: {filepath} ({size} bytes)")
        else:
            click.echo(f"❌ {description}: {filepath} (missing)")
            all_exist = False

    if all_exist:
        click.echo("\n✅ All required certificates are present")

        # Try to verify the certificate chain
        try:
            result = run_command([
                "openssl", "verify", "-CAfile",
                str(CERTS_DIR / "ca.crt"),
                str(CERTS_DIR / "server.crt")
            ], check=False)

            if result.returncode == 0:
                click.echo("✅ Certificate chain is valid")
            else:
                click.echo("⚠️  Certificate chain verification failed")
                click.echo(result.stderr)
        except FileNotFoundError:
            click.echo("ℹ️  OpenSSL not found, skipping certificate verification")
    else:
        click.echo("\n❌ Some certificates are missing")
        click.echo("Run 'ldap-docker certs generate' to create them")
        sys.exit(1)


@cli.group()
def test():
    """Test LDAP server connectivity and queries."""
    pass


@test.command("connection")
@click.option("--host", default=DEFAULT_HOST, help="LDAP server host")
@click.option("--port", default=DEFAULT_PORT, help="LDAP server port")
@click.option("--use-ssl", is_flag=True, help="Use LDAPS instead of LDAP")
def test_connection(host: str, port: int, use_ssl: bool):
    """Test basic connection to LDAP server."""
    if ldap3 is None:
        click.echo("Error: ldap3 library not installed", err=True)
        click.echo("Install it with: uv pip install ldap3", err=True)
        sys.exit(1)

    if use_ssl:
        port = DEFAULT_LDAPS_PORT
        url = f"ldaps://{host}:{port}"
    else:
        url = f"ldap://{host}:{port}"

    click.echo(f"Testing connection to {url}...")

    try:
        server = Server(url, get_info=ALL, use_ssl=use_ssl)
        conn = Connection(server, auto_bind=True)

        click.echo("✅ Successfully connected to LDAP server")
        click.echo(f"\nServer info:")
        click.echo(f"  Vendor: {server.info.vendor_name if server.info else 'Unknown'}")
        click.echo(f"  Version: {server.info.vendor_version if server.info else 'Unknown'}")

        conn.unbind()

    except LDAPException as e:
        click.echo(f"❌ Connection failed: {e}", err=True)
        sys.exit(1)


@test.command("auth")
@click.option("--host", default=DEFAULT_HOST, help="LDAP server host")
@click.option("--port", default=DEFAULT_PORT, help="LDAP server port")
@click.option("--use-ssl", is_flag=True, help="Use LDAPS")
@click.option("--user", default=DEFAULT_ADMIN_DN, help="User DN")
@click.option("--password", default=DEFAULT_ADMIN_PASSWORD, help="Password")
def test_auth(host: str, port: int, use_ssl: bool, user: str, password: str):
    """Test authentication with LDAP server."""
    if ldap3 is None:
        click.echo("Error: ldap3 library not installed", err=True)
        click.echo("Install it with: uv pip install ldap3", err=True)
        sys.exit(1)

    if use_ssl:
        port = DEFAULT_LDAPS_PORT
        url = f"ldaps://{host}:{port}"
    else:
        url = f"ldap://{host}:{port}"

    click.echo(f"Testing authentication to {url}...")
    click.echo(f"User: {user}")

    try:
        server = Server(url, get_info=ALL, use_ssl=use_ssl)
        conn = Connection(server, user=user, password=password, auto_bind=True)

        click.echo("✅ Authentication successful")

        # Try to perform a simple search
        conn.search(DEFAULT_BASE_DN, "(objectClass=*)", search_scope="BASE")
        if conn.entries:
            click.echo(f"✅ Base DN accessible: {DEFAULT_BASE_DN}")

        conn.unbind()

    except LDAPException as e:
        click.echo(f"❌ Authentication failed: {e}", err=True)
        sys.exit(1)


@test.command("users")
@click.option("--host", default=DEFAULT_HOST, help="LDAP server host")
@click.option("--port", default=DEFAULT_PORT, help="LDAP server port")
@click.option("--use-ssl", is_flag=True, help="Use LDAPS")
def test_users(host: str, port: int, use_ssl: bool):
    """List all users in the LDAP directory."""
    if ldap3 is None:
        click.echo("Error: ldap3 library not installed", err=True)
        click.echo("Install it with: uv pip install ldap3", err=True)
        sys.exit(1)

    if use_ssl:
        port = DEFAULT_LDAPS_PORT
        url = f"ldaps://{host}:{port}"
    else:
        url = f"ldap://{host}:{port}"

    try:
        server = Server(url, get_info=ALL, use_ssl=use_ssl)
        conn = Connection(
            server,
            user=DEFAULT_ADMIN_DN,
            password=DEFAULT_ADMIN_PASSWORD,
            auto_bind=True
        )

        # Search for all users
        conn.search(
            DEFAULT_BASE_DN,
            "(objectClass=inetOrgPerson)",
            attributes=["uid", "cn", "mail", "uidNumber"]
        )

        if conn.entries:
            click.echo(f"Found {len(conn.entries)} user(s):\n")
            for entry in conn.entries:
                click.echo(f"  - {entry.cn}: {entry.uid} ({entry.mail})")
        else:
            click.echo("No users found")

        conn.unbind()

    except LDAPException as e:
        click.echo(f"❌ Query failed: {e}", err=True)
        sys.exit(1)


@cli.command("init")
def init():
    """Initialize the LDAP Docker environment."""
    click.echo("Initializing LDAP Docker environment...\n")

    # Check Docker
    click.echo("1. Checking Docker...")
    check_docker()
    click.echo("   ✅ Docker is available\n")

    # Check certificates
    click.echo("2. Checking SSL certificates...")
    if not check_certificates():
        if click.confirm("\nGenerate self-signed certificates now?", default=True):
            certs_generate.callback(force=False, hostname="ldap.testing.local")
        else:
            click.echo("\nℹ️  You can generate certificates later with: ldap-docker certs generate")
            click.echo("   Or copy your dev-ca certificates to the certs/ directory")
    else:
        click.echo("   ✅ Certificates are present\n")

    # Start server
    click.echo("\n3. Starting LDAP server...")
    if click.confirm("Start the LDAP server now?", default=True):
        server_start.callback(detach=True, build=False)
    else:
        click.echo("\nℹ️  You can start the server later with: ldap-docker server start")

    click.echo("\n✅ Initialization complete!")
    click.echo("\nUseful commands:")
    click.echo("  - View logs: ldap-docker server logs -f")
    click.echo("  - Test connection: ldap-docker test connection")
    click.echo("  - List users: ldap-docker test users")
    click.echo("  - Stop server: ldap-docker server stop")


def main():
    """Entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
