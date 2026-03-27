.PHONY: help dev test lint build deploy clean logs

help:
	@echo "HandTalk - Production-Ready Sign Language Recognition"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start development environment"
	@echo "  make test             Run all tests"
	@echo "  make lint             Run linting"
	@echo ""
	@echo "Production:"
	@echo "  make build            Build Docker images"
	@echo "  make deploy           Deploy to production"
	@echo "  make logs             View production logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Stop containers & remove volumes"
	@echo ""

dev:
	@echo "🚀 Starting development environment..."
	docker-compose -f config/docker-compose.yml up

dev-down:
	@echo "⏹️  Stopping development environment..."
	docker-compose -f config/docker-compose.yml down

test:
	@echo "🧪 Running tests..."
	./scripts/test.sh

lint:
	@echo "🧹 Running linting..."
	./scripts/lint.sh

build:
	@echo "🐳 Building Docker images..."
	./scripts/build.sh

deploy:
	@echo "🚀 Deploying to production..."
	./scripts/deploy.sh config/docker-compose.prod.yml config/.env.production

logs:
	@echo "📋 Production logs..."
	docker-compose -f config/docker-compose.prod.yml logs -f

clean:
	@echo "🧹 Cleaning up..."
	docker-compose -f config/docker-compose.yml down -v
	docker-compose -f config/docker-compose.prod.yml down -v
	docker system prune -f

install:
	@echo "📦 Installing dependencies..."
	cd apps/api && pip install -r requirements.txt -r requirements-dev.txt
	cd ../web && npm install
	cd ../..

format:
	@echo "🎨 Formatting code..."
	cd apps/api && black . && isort . && cd ../..
	cd apps/web && npm run lint -- --fix && cd ../..

docs:
	@echo "📖 Documentation files:"
	@echo "  docs/SETUP.md               - Development setup"
	@echo "  docs/TESTING.md             - Running tests"
	@echo "  docs/TROUBLESHOOTING.md     - Common issues"
	@echo "  docs/DEPLOYMENT.md          - Production deployment"

shell-api:
	@echo "🐍 Opening Python shell in API container..."
	docker-compose -f config/docker-compose.yml exec api /bin/bash

shell-web:
	@echo "📦 Opening shell in Web container..."
	docker-compose -f config/docker-compose.yml exec web /bin/sh

status:
	@echo "📊 Container status:"
	docker-compose -f config/docker-compose.yml ps

health:
	@echo "🏥 Health checks:"
	@curl -s http://localhost:8001/health || echo "❌ API health check failed"
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Web app is running" || echo "❌ Web app not responding"
