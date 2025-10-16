.PHONY: help install init start stop restart down logs status certs-generate certs-check test-connection test-auth test-users clean clean-all

# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help message
	@echo "LDAP Docker Development Tool"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python dependencies with UV
	@echo "Installing dependencies with UV..."
	@command -v uv >/dev/null 2>&1 || { echo "Error: uv not found. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
	uv sync
	@echo "✅ Dependencies installed"

install-dev:  ## Install development dependencies
	@echo "Installing development dependencies with UV..."
	uv sync --all-extras
	@echo "✅ Development dependencies installed"

init: install certs-check  ## Initialize the environment (install deps, check certs)
	@echo ""
	@echo "Initialization complete!"
	@echo "Run 'make start' to start the LDAP server"

certs-generate:  ## Generate self-signed SSL certificates
	@echo "Generating SSL certificates..."
	uv run python scripts/generate_certs.py
	@echo "✅ Certificates generated"

certs-check:  ## Check if SSL certificates exist
	@echo "Checking SSL certificates..."
	@if [ ! -f certs/ca.crt ] || [ ! -f certs/server.crt ] || [ ! -f certs/server.key ]; then \
		echo "⚠️  Warning: SSL certificates not found"; \
		echo ""; \
		echo "You can:"; \
		echo "  1. Copy your dev-ca certificates to certs/"; \
		echo "     cp /path/to/dev-ca/ca.crt certs/"; \
		echo "     cp /path/to/dev-ca/server.crt certs/"; \
		echo "     cp /path/to/dev-ca/server.key certs/"; \
		echo "  2. Generate self-signed certs: make certs-generate"; \
		echo ""; \
		exit 1; \
	else \
		echo "✅ SSL certificates found"; \
	fi

start:  ## Start the LDAP server
	@echo "Starting LDAP server..."
	docker-compose up -d
	@echo "✅ LDAP server started"
	@echo ""
	@echo "Services available at:"
	@echo "  - LDAP:  ldap://localhost:$${LDAP_PORT:-389}"
	@echo "  - LDAPS: ldaps://localhost:$${LDAPS_PORT:-636}"
	@echo "  - Admin: http://localhost:$${PHPLDAPADMIN_PORT:-8080}"
	@echo ""
	@echo "Admin credentials:"
	@echo "  DN: cn=admin,dc=testing,dc=local"
	@echo "  Password: admin_password"
	@echo ""
	@echo "Run 'make logs' to view logs"

stop:  ## Stop the LDAP server
	@echo "Stopping LDAP server..."
	docker-compose stop
	@echo "✅ LDAP server stopped"

restart:  ## Restart the LDAP server
	@echo "Restarting LDAP server..."
	docker-compose restart
	@echo "✅ LDAP server restarted"

down:  ## Stop and remove containers (keeps data)
	@echo "Stopping and removing containers..."
	docker-compose down
	@echo "✅ Containers removed (data preserved)"

down-volumes:  ## Stop and remove containers AND volumes (deletes all data)
	@echo "⚠️  WARNING: This will delete all LDAP data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "✅ Containers and volumes removed"; \
	else \
		echo "Aborted"; \
	fi

logs:  ## View LDAP server logs (follow mode)
	docker-compose logs -f openldap

logs-tail:  ## View last 100 lines of logs
	docker-compose logs --tail=100 openldap

logs-admin:  ## View phpLDAPadmin logs
	docker-compose logs -f phpldapadmin

status:  ## Show container status
	@docker-compose ps

test-connection:  ## Test connection to LDAP server
	@echo "Testing LDAP connection..."
	@export LDAP_PORT=$${LDAP_PORT:-389}; uv run python -c "import os; from ldap3 import Server, Connection, ALL; s = Server(f\"ldap://localhost:{os.environ.get('LDAP_PORT', '389')}\", get_info=ALL); c = Connection(s, auto_bind=True); print('✅ Connection successful'); c.unbind()"

test-auth:  ## Test authentication with admin user
	@echo "Testing LDAP authentication..."
	@export LDAP_PORT=$${LDAP_PORT:-389}; uv run python -c "import os; from ldap3 import Server, Connection; s = Server(f\"ldap://localhost:{os.environ.get('LDAP_PORT', '389')}\"); c = Connection(s, 'cn=admin,dc=testing,dc=local', 'admin_password', auto_bind=True); print('✅ Authentication successful'); c.unbind()"

test-users:  ## List all users in LDAP
	@echo "Listing LDAP users..."
	@export LDAP_PORT=$${LDAP_PORT:-389}; uv run python -c "import os; from ldap3 import Server, Connection; s = Server(f\"ldap://localhost:{os.environ.get('LDAP_PORT', '389')}\"); c = Connection(s, 'cn=admin,dc=testing,dc=local', 'admin_password', auto_bind=True); c.search('dc=testing,dc=local', '(objectClass=inetOrgPerson)', attributes=['uid', 'cn', 'mail']); [print(f'  - {e.cn}: {e.uid} ({e.mail})') for e in c.entries]; c.unbind()"

test-ssl:  ## Test SSL/TLS connection
	@echo "Testing LDAPS connection..."
	openssl s_client -connect localhost:$${LDAPS_PORT:-636} -CAfile certs/ca.crt </dev/null

test-all: test-connection test-auth test-users  ## Run all tests

shell:  ## Open a shell in the LDAP container
	docker-compose exec openldap bash

ldapsearch:  ## Run ldapsearch command (example query)
	@echo "Running ldapsearch..."
	ldapsearch -H ldap://localhost:$${LDAP_PORT:-389} -x -b "dc=testing,dc=local" -D "cn=admin,dc=testing,dc=local" -w admin_password

clean:  ## Clean Python build artifacts
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf build/ dist/ .eggs/
	@echo "✅ Cleaned"

clean-all: clean down-volumes  ## Clean everything including Docker volumes
	@echo "Cleaning certificates (keeping README)..."
	find certs/ -type f ! -name "README.md" -delete 2>/dev/null || true
	@echo "✅ Full cleanup complete"

dev-setup: install-dev certs-generate start  ## Complete development setup
	@echo ""
	@echo "🎉 Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  - View logs: make logs"
	@echo "  - Test connection: make test-connection"
	@echo "  - List users: make test-users"
	@echo "  - Open admin UI: open http://localhost:8080"

quick-start: certs-check start  ## Quick start (assumes certs exist)
	@echo "🚀 LDAP server is running!"

rebuild: down  ## Rebuild and restart containers
	@echo "Rebuilding containers..."
	docker-compose up -d --build
	@echo "✅ Containers rebuilt and started"

# UV-specific targets
uv-install:  ## Install UV package manager
	@echo "Installing UV..."
	@command -v uv >/dev/null 2>&1 && echo "✅ UV already installed" || curl -LsSf https://astral.sh/uv/install.sh | sh

uv-sync:  ## Sync dependencies with UV
	uv sync

uv-update:  ## Update all dependencies
	uv lock --upgrade
	uv sync

# Docker checks
check-docker:  ## Check if Docker is running
	@docker version >/dev/null 2>&1 && echo "✅ Docker is running" || (echo "❌ Docker is not running. Please start Docker or Rancher Desktop." && exit 1)

check-compose:  ## Check if docker-compose is available
	@docker-compose version >/dev/null 2>&1 && echo "✅ docker-compose is available" || (echo "❌ docker-compose not found" && exit 1)

check-all: check-docker check-compose certs-check  ## Run all checks
	@echo "✅ All checks passed"
