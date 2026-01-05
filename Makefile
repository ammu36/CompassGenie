# --- Variables ---
# Use 'python' on Windows, 'python3' on Mac/Linux
PYTHON = python
APP_NAME = app.main:app
VENV_BIN = cg3.12venv/Scripts

# --- Help (Default target) ---
.PHONY: help
help:
	@echo "CompassGenie Control Panel:"
	@echo "  make install  - Install dependencies locally"
	@echo "  make dev      - Run backend locally (hot-reload)"
	@echo "  make test     - Run all tests (Unit + Integration)"
	@echo "  make lint     - Run code quality checks (Ruff)"
	@echo "  make build    - Build and start Docker containers"
	@echo "  make stop     - Stop all Docker containers"
	@echo "  make clean    - Remove temporary files and caches"

# --- Local Development ---
.PHONY: install
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install pytest ruff

.PHONY: dev
dev:
	uvicorn $(APP_NAME) --reload --port 8000

# --- Testing & Quality ---
.PHONY: test
test:
	$(PYTHON) -m pytest -v tests/

.PHONY: lint
lint:
	ruff check .
	ruff format .

# --- Docker ---
.PHONY: build
build:
	docker-compose up --build

.PHONY: stop
stop:
	docker-compose down

# --- Cleanup ---
.PHONY: clean
clean:
	@if exist "__pycache__" rd /s /q __pycache__
	@if exist ".pytest_cache" rd /s /q .pytest_cache
	@if exist ".ruff_cache" rd /s /q .ruff_cache
	@echo "Cleanup complete."