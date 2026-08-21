.PHONY: install test api worker status
install:
	python -m pip install -e ".[dev]"
test:
	pytest -q
api:
	uvicorn jobpilot.api.main:app --reload --port 8000
status:
	jobpilot status
seed:
	jobpilot seed
cycle:
	jobpilot cycle --no-scout
compose:
	docker compose up --build
gcp-deploy:
	./scripts/gcp-deploy.sh
