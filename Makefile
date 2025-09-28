PYTHON ?= python3

.PHONY: dev-up dev-down migrate logs ps install-dev fmt fmt-check lint typecheck test check audit secrets coverage

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
	$(PYTHON) -m black src tests

fmt-check:
	$(PYTHON) -m black --check src tests

lint:
	$(PYTHON) -m ruff check src tests

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing

coverage:
	$(PYTHON) -m coverage html

secrets:
	$(PYTHON) -m pip install --upgrade gitleaks && gitleaks detect --no-banner

audit:
	$(PYTHON) -m pip install pip-audit && pip-audit -r pyproject.toml

check: fmt-check lint typecheck test
