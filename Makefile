.PHONY: help up down logs ps dev-web test-web build-web init-hooks

# Help target listing available commands
help:
	@echo "Growixa Management Commands:"
	@echo "  make up         - Build and start all Docker services in background"
	@echo "  make down       - Stop and remove all Docker containers"
	@echo "  make logs       - Stream live logs from all Docker containers"
	@echo "  make ps         - Show status of running Docker containers"
	@echo "  make dev-web    - Run Next.js local development server (apps/web)"
	@echo "  make test-web   - Run Vitest component tests (apps/web)"
	@echo "  make build-web  - Run production build for frontend (apps/web)"
	@echo "  make init-hooks - Install & activate local Git pre-push hooks"

# Developer Setup targets
init-hooks:
	chmod +x scripts/check_branch_name.sh
	pre-commit install
	pre-commit install --hook-type pre-push
	@echo "✅ Pre-commit hooks installed (main protection & branch naming enforcement active)"

# Docker Compose targets
up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

# Web App targets
dev-web:
	cd apps/web && npm run dev

test-web:
	cd apps/web && npm run test -- --run

build-web:
	cd apps/web && npm run build
