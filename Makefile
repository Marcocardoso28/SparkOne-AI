PYTHON ?= python3

.PHONY: dev-up dev-down migrate logs ps install-dev fmt fmt-check lint typecheck test check

dev-up:
	docker compose up --build

dev-down:
	docker compose down

migrate:
	docker compose exec api alembic upgrade head

logs:
	docker compose logs -f api

ps:
	docker compose ps

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

fmt:
	$(PYTHON) -m black src

fmt-check:
	$(PYTHON) -m black --check src

lint:
	$(PYTHON) -m ruff check src

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest

check: fmt-check lint typecheck test
