# ELF Automations - Virtual AI Company Platform
# Development and deployment automation

.PHONY: help setup install test lint format clean docker-up docker-down k8s-setup k8s-clean

# Default target
help: ## Show this help message
	@echo "ELF Automations - Virtual AI Company Platform"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment setup
setup: ## Set up the development environment
	@echo "Setting up development environment..."
	conda activate ElfAutomations || (echo "Please activate ElfAutomations conda environment first" && exit 1)
	pip install -r requirements.txt
	pre-commit install
	@echo "Development environment setup complete!"

install: setup ## Install all dependencies and tools
	@echo "Installing additional tools..."
	./tools/bin/kagent version || (echo "kagent not found, please check installation" && exit 1)
	@echo "All tools installed successfully!"

# Code quality
test: ## Run all tests
	@echo "Running tests..."
	conda activate ElfAutomations && python -m pytest tests/ -v --cov=agents --cov=workflows --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	conda activate ElfAutomations && python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	conda activate ElfAutomations && python -m pytest tests/integration/ -v

lint: ## Run linting checks
	@echo "Running linting checks..."
	conda activate ElfAutomations && flake8 .
	conda activate ElfAutomations && mypy .
	conda activate ElfAutomations && bandit -r . -f json -o bandit-report.json

format: ## Format code with black and isort
	@echo "Formatting code..."
	conda activate ElfAutomations && black .
	conda activate ElfAutomations && isort .

pre-commit: ## Run pre-commit hooks on all files
	@echo "Running pre-commit hooks..."
	conda activate ElfAutomations && pre-commit run --all-files

# Local development services
docker-up: ## Start local development services (PostgreSQL, Redis, etc.)
	@echo "Starting local development services..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Services are ready!"

docker-down: ## Stop local development services
	@echo "Stopping local development services..."
	docker-compose down

docker-logs: ## Show logs from development services
	docker-compose logs -f

docker-clean: ## Clean up Docker containers and volumes
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f

# Kubernetes setup
k8s-setup: ## Set up Kubernetes cluster and install kagent
	@echo "Setting up Kubernetes cluster..."
	minikube status || minikube start --driver=docker --memory=6144 --cpus=3
	kubectl cluster-info
	@echo "Installing kagent..."
	./tools/bin/kagent install || echo "kagent installation may require manual setup"
	@echo "Kubernetes setup complete!"

k8s-clean: ## Clean up Kubernetes resources
	@echo "Cleaning up Kubernetes resources..."
	kubectl delete namespace elf-automations --ignore-not-found=true
	minikube stop

k8s-status: ## Show Kubernetes cluster status
	@echo "Kubernetes cluster status:"
	kubectl cluster-info
	kubectl get nodes
	kubectl get pods --all-namespaces

# Database operations
db-init: ## Initialize database with schema
	@echo "Initializing database..."
	docker-compose exec postgres psql -U elfuser -d elfautomations -f /docker-entrypoint-initdb.d/init-db.sql
	@echo "Database initialized!"

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "Resetting database..."
	docker-compose down postgres
	docker volume rm elfautomations_postgres_data || true
	docker-compose up -d postgres
	sleep 5
	make db-init
	@echo "Database reset complete!"

# Development
dev: docker-up ## Start development environment
	@echo "Starting development environment..."
	@echo "Services available at:"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Jaeger: http://localhost:16686"

run-chief: ## Run the Chief AI Agent locally
	@echo "Starting Chief AI Agent..."
	conda activate ElfAutomations && python -m agents.executive.chief_ai_agent

run-api: ## Run the API server locally
	@echo "Starting API server..."
	conda activate ElfAutomations && uvicorn apis.main:app --reload --host 0.0.0.0 --port 8000

# Monitoring
logs: ## Show application logs
	@echo "Showing application logs..."
	docker-compose logs -f

metrics: ## Open Prometheus metrics dashboard
	@echo "Opening Prometheus at http://localhost:9090"
	open http://localhost:9090

dashboards: ## Open Grafana dashboards
	@echo "Opening Grafana at http://localhost:3000"
	open http://localhost:3000

tracing: ## Open Jaeger tracing UI
	@echo "Opening Jaeger at http://localhost:16686"
	open http://localhost:16686

# Cleanup
clean: ## Clean up all temporary files and caches
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -f bandit-report.json
	@echo "Cleanup complete!"

clean-all: clean docker-clean k8s-clean ## Clean up everything (Docker, Kubernetes, temp files)
	@echo "Full cleanup complete!"

# Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	# Add documentation generation commands here
	@echo "Documentation generated!"

# Deployment
deploy-local: k8s-setup ## Deploy to local Kubernetes cluster
	@echo "Deploying to local Kubernetes..."
	kubectl apply -f k8s/base/
	@echo "Local deployment complete!"

# Version info
version: ## Show version information
	@echo "ELF Automations Version Information:"
	@echo "Python: $(shell python --version)"
	@echo "Docker: $(shell docker --version)"
	@echo "Kubernetes: $(shell kubectl version --client --short)"
	@echo "kagent: $(shell ./tools/bin/kagent version | head -1)"
	@echo "Minikube: $(shell minikube version --short)"

# Quick start
quickstart: setup docker-up k8s-setup ## Quick start for new developers
	@echo "🚀 ELF Automations Quick Start Complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.template to .env and fill in your API keys"
	@echo "2. Run 'make dev' to start development services"
	@echo "3. Run 'make run-api' to start the API server"
	@echo "4. Run 'make run-chief' to start the Chief AI Agent"
	@echo ""
	@echo "Useful commands:"
	@echo "  - make test: Run tests"
	@echo "  - make format: Format code"
	@echo "  - make metrics: Open monitoring dashboard"
	@echo "  - make help: Show all available commands"
