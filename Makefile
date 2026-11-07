.PHONY: dev test seed down demo-test

dev:
	docker compose up --build

test:
	cd backend && ../.venv/bin/ruff check . && ../.venv/bin/pytest
	cd frontend && npm run build
	cd frontend && npm run test:e2e

demo-test:
	cd frontend && npm run test:e2e

seed:
	docker compose run --rm seed

down:
	docker compose down
