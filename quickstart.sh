#!/usr/bin/env bash
#
# Quick Start Script for LDAP Docker
# This script will guide you through setting up and starting the LDAP server
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emoji support (works on most terminals)
CHECK_MARK="✅"
CROSS_MARK="❌"
WARNING="⚠️"
ROCKET="🚀"
GEAR="⚙️"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}${CHECK_MARK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS_MARK} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_info() {
    echo -e "${BLUE}${GEAR} $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Docker
check_docker() {
    print_info "Checking Docker..."

    if command_exists docker; then
        if docker version >/dev/null 2>&1; then
            print_success "Docker is installed and running"
            return 0
        else
            print_error "Docker is installed but not running"
            echo ""
            echo "Please start Docker or Rancher Desktop and try again."
            return 1
        fi
    else
        print_error "Docker is not installed"
        echo ""
        echo "Please install one of the following:"
        echo "  - Rancher Desktop (recommended for MacOS): https://rancherdesktop.io/"
        echo "  - Docker Desktop: https://www.docker.com/products/docker-desktop"
        return 1
    fi
}

# Check docker-compose
check_docker_compose() {
    print_info "Checking docker-compose..."

    if command_exists docker-compose; then
        print_success "docker-compose is available"
        return 0
    elif docker compose version >/dev/null 2>&1; then
        print_success "docker compose (v2) is available"
        return 0
    else
        print_warning "docker-compose not found"
        echo "Docker Compose is usually included with Docker Desktop and Rancher Desktop."
        echo "If you're using a standalone Docker installation, please install docker-compose."
        return 1
    fi
}

# Check Python
check_python() {
    print_info "Checking Python..."

    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python ${PYTHON_VERSION} is installed"
        return 0
    elif command_exists python; then
        PYTHON_VERSION=$(python --version | cut -d' ' -f2)
        print_success "Python ${PYTHON_VERSION} is installed"
        return 0
    else
        print_error "Python is not installed"
        echo "Please install Python 3.9 or higher."
        return 1
    fi
}

# Check/Install UV
check_install_uv() {
    print_info "Checking UV package manager..."

    if command_exists uv; then
        UV_VERSION=$(uv --version | cut -d' ' -f2 || echo "unknown")
        print_success "UV ${UV_VERSION} is installed"
        return 0
    else
        print_warning "UV is not installed"
        echo ""
        echo "UV is a fast Python package manager (recommended for this project)."
        read -p "Would you like to install UV now? [Y/n] " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            print_info "Installing UV..."
            curl -LsSf https://astral.sh/uv/install.sh | sh

            # Source the shell config to get UV in PATH
            export PATH="$HOME/.cargo/bin:$PATH"

            if command_exists uv; then
                print_success "UV installed successfully"
                return 0
            else
                print_error "UV installation may have completed but it's not in PATH"
                echo "Please restart your terminal and run this script again."
                return 1
            fi
        else
            print_warning "Skipping UV installation"
            echo "You can install dependencies manually with pip if needed."
            return 1
        fi
    fi
}

# Check certificates
check_certificates() {
    print_info "Checking SSL certificates..."

    if [[ -f "certs/ca.crt" && -f "certs/server.crt" && -f "certs/server.key" ]]; then
        print_success "SSL certificates found"
        return 0
    else
        print_warning "SSL certificates not found"
        return 1
    fi
}

# Generate certificates
generate_certificates() {
    print_info "Generating SSL certificates..."

    if command_exists uv && [[ -f "scripts/generate_certs.py" ]]; then
        uv run python scripts/generate_certs.py
        print_success "Certificates generated"
    elif command_exists python3; then
        python3 scripts/generate_certs.py
        print_success "Certificates generated"
    else
        print_error "Cannot generate certificates - Python not available"
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."

    if command_exists uv; then
        uv sync
        print_success "Dependencies installed with UV"
    elif command_exists python3 && command_exists pip3; then
        pip3 install -e .
        print_success "Dependencies installed with pip"
    else
        print_warning "Cannot install dependencies automatically"
        echo "Please install dependencies manually."
        return 1
    fi
}

# Start LDAP server
start_server() {
    print_info "Starting LDAP server..."

    if command_exists docker-compose; then
        docker-compose up -d
    else
        docker compose up -d
    fi

    print_success "LDAP server started"

    # Wait a bit for the server to initialize
    print_info "Waiting for server to initialize (10 seconds)..."
    sleep 10
}

# Test connection
test_connection() {
    print_info "Testing LDAP connection..."

    # Simple check if container is running
    if docker ps | grep -q "ldap-server"; then
        print_success "LDAP server container is running"
        return 0
    else
        print_warning "LDAP server container may not be fully started yet"
        return 1
    fi
}

# Print final information
print_final_info() {
    echo ""
    print_header "${ROCKET} LDAP Server is Ready! ${ROCKET}"

    echo "Services are now available at:"
    echo ""
    echo "  ${GREEN}LDAP:${NC}  ldap://localhost:389"
    echo "  ${GREEN}LDAPS:${NC} ldaps://localhost:636"
    echo "  ${GREEN}Admin UI:${NC} http://localhost:8080"
    echo ""
    echo "Admin Credentials:"
    echo "  ${BLUE}DN:${NC}       cn=admin,dc=testing,dc=local"
    echo "  ${BLUE}Password:${NC} admin_password"
    echo ""
    echo "Test Users (password: password123):"
    echo "  - jdoe (John Doe)"
    echo "  - jsmith (Jane Smith)"
    echo "  - testuser (Test User)"
    echo ""
    echo "Useful Commands:"
    echo "  ${BLUE}make logs${NC}          - View server logs"
    echo "  ${BLUE}make test-users${NC}    - List all users"
    echo "  ${BLUE}make status${NC}        - Check server status"
    echo "  ${BLUE}make stop${NC}          - Stop the server"
    echo "  ${BLUE}make help${NC}          - See all available commands"
    echo ""
    echo "Documentation:"
    echo "  - README.md for full documentation"
    echo "  - certs/README.md for certificate management"
    echo ""
}

# Main script
main() {
    clear
    print_header "${ROCKET} LDAP Docker Quick Start ${ROCKET}"

    echo "This script will set up and start your LDAP development server."
    echo ""

    # Step 1: Check prerequisites
    print_header "Step 1: Checking Prerequisites"

    PREREQ_OK=true

    check_docker || PREREQ_OK=false
    check_docker_compose || PREREQ_OK=false
    check_python || PREREQ_OK=false

    if [ "$PREREQ_OK" = false ]; then
        echo ""
        print_error "Some prerequisites are missing. Please install them and try again."
        exit 1
    fi

    echo ""
    print_success "All prerequisites are met!"
    echo ""

    # Step 2: UV installation (optional but recommended)
    print_header "Step 2: Package Manager Setup"
    check_install_uv
    HAS_UV=$?
    echo ""

    # Step 3: SSL Certificates
    print_header "Step 3: SSL Certificate Setup"

    if check_certificates; then
        echo ""
        print_info "Existing certificates will be used."
        read -p "Regenerate certificates? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            generate_certificates
        fi
    else
        echo ""
        echo "SSL certificates are required for LDAPS (secure LDAP)."
        echo ""
        echo "You can:"
        echo "  1. Generate self-signed certificates now (recommended for quick start)"
        echo "  2. Copy certificates from your dev-ca manually to certs/"
        echo ""
        read -p "Generate self-signed certificates now? [Y/n] " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            generate_certificates
        else
            print_info "Please copy your certificates to certs/ directory:"
            echo "  - certs/ca.crt"
            echo "  - certs/server.crt"
            echo "  - certs/server.key"
            echo ""
            read -p "Press Enter when ready to continue..."

            if ! check_certificates; then
                print_error "Certificates still not found. Exiting."
                exit 1
            fi
        fi
    fi

    echo ""

    # Step 4: Install dependencies (optional)
    if [ $HAS_UV -eq 0 ]; then
        print_header "Step 4: Installing Dependencies"
        install_dependencies
        echo ""
    else
        print_info "Skipping dependency installation (UV not available)"
        echo ""
    fi

    # Step 5: Start server
    print_header "Step 5: Starting LDAP Server"
    start_server
    echo ""

    # Step 6: Test
    print_header "Step 6: Verifying Installation"
    test_connection
    echo ""

    # Success!
    print_final_info

    # Offer to view logs
    echo ""
    read -p "View server logs now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        print_info "Showing logs (press Ctrl+C to exit)..."
        sleep 2
        if command_exists docker-compose; then
            docker-compose logs -f openldap
        else
            docker compose logs -f openldap
        fi
    fi
}

# Run main function
main

exit 0
