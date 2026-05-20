.PHONY: dev test build sync-design migrate fresh-db format lint

sync-design:
	python scripts/sync-design.py

dev: sync-design
	FLASK_ENV=development flask --app app run --debug --port 5000

test:
	pytest -v

migrate:
	flask --app app db upgrade

fresh-db:
	rm -f grogblossoms.db
	flask --app app db upgrade

format:
	black app tests scripts
	ruff check --fix app tests scripts

lint:
	ruff check app tests scripts
	black --check app tests scripts

build:
	docker build -t mm-grogblossoms:dev .
