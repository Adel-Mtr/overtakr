.PHONY: install dev-backend dev-frontend test lint typecheck build docker-up docker-down

install:
	cd backend && python -m pip install -r requirements-dev.txt
	cd frontend && npm ci

dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -q

lint:
	cd frontend && npm run lint

typecheck:
	cd frontend && npm run typecheck

build:
	cd frontend && npm run build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
