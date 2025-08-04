# Financial Tracker Makefile
# Provides convenient commands for development tasks

.PHONY: help install run test format lint quality setup-dev clean

# Default target
help:
	@echo "Financial Tracker Development Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  setup-dev   Set up development environment with sample data"
	@echo ""
	@echo "Development:"
	@echo "  run         Run the development server"
	@echo "  test        Run the test suite"
	@echo "  test-cov    Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  format      Format code with Black"
	@echo "  lint        Lint code with Flake8"
	@echo "  quality     Run all quality checks (format + lint + test)"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       Clean up temporary files"
	@echo ""

# Installation
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 selenium

# Development server
run:
	@echo "Starting development server..."
	python run.py run

run-prod:
	@echo "Starting production server..."
	python run.py run --config production --no-debug

# Testing
test:
	@echo "Running test suite..."
	python run.py test

test-cov:
	@echo "Running test suite with coverage..."
	python run.py test --coverage

test-verbose:
	@echo "Running test suite (verbose)..."
	python run.py test --verbose

# Code quality
format:
	@echo "Formatting code..."
	python run.py format

lint:
	@echo "Linting code..."
	python run.py lint

quality:
	@echo "Running all quality checks..."
	python run.py quality

quality-cov:
	@echo "Running all quality checks with coverage..."
	python run.py quality --coverage

# Development setup
setup-dev:
	@echo "Setting up development environment..."
	python run.py setup-dev

# Database management
reset-db:
	@echo "Resetting database..."
	rm -f financial_tracker.db
	@echo "Database reset. Run 'make setup-dev' to recreate with sample data."

# Maintenance
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	@echo "Cleanup complete."

# Docker commands (if Docker support is added later)
docker-build:
	@echo "Building Docker image..."
	docker build -t financial-tracker .

docker-run:
	@echo "Running Docker container..."
	docker run -p 5000:5000 financial-tracker

# Backup and restore
backup-db:
	@echo "Creating database backup..."
	cp financial_tracker.db financial_tracker_backup_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Backup created."

# Quick development workflow
dev: clean install setup-dev
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the server."

# CI/CD simulation
ci: quality-cov
	@echo "CI checks passed!"

# Show project status
status:
	@echo "Financial Tracker Project Status"
	@echo "==============================="
	@echo ""
	@echo "Python version:"
	@python --version
	@echo ""
	@echo "Dependencies status:"
	@pip list | grep -E "(flask|sqlalchemy|yfinance|pytest)" || echo "Dependencies not installed"
	@echo ""
	@echo "Database status:"
	@if [ -f financial_tracker.db ]; then echo "Database exists"; else echo "Database not found"; fi
	@echo ""
	@echo "Test status:"
	@python -m pytest --collect-only -q 2>/dev/null | tail -1 || echo "Tests not available"

# Development shortcuts
dev-run: setup-dev run
dev-test: format lint test
