.PHONY: install test run docker-up docker-down lint demo clean

install:
	pip install -r backend/requirements.txt

test:
	pytest tests/ -v --tb=short

run:
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v

lint:
	pylint backend/ --disable=C0114,C0115,C0116 --fail-under=5.0

demo:
	bash scripts/demo.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
