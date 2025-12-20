.PHONY: help install-backend install-frontend install backend frontend setup clean

help:
	@echo "🚀 Auto Semantic Project - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install all dependencies (backend + frontend)"
	@echo "  make install-backend  - Install backend Python dependencies"
	@echo "  make install-frontend - Install frontend Node.js dependencies"
	@echo "  make setup            - Complete setup with env check"
	@echo ""
	@echo "Running:"
	@echo "  make backend          - Start backend server (port 8000)"
	@echo "  make frontend         - Start frontend server (port 3000)"
	@echo ""
	@echo "Semantic Layer:"
	@echo "  make generate-semantic - Generate semantic layer from DBT manifest"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            - Clean generated files and caches"
	@echo "  make test             - Run tests (if available)"
	@echo ""

install: install-backend install-frontend
	@echo "✅ All dependencies installed successfully!"

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && python3 -m venv venv && \
	. venv/bin/activate && \
	pip install -r requirements.txt
	@echo "✅ Backend dependencies installed!"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed!"

setup: install
	@echo ""
	@echo "⚙️  Setup Complete!"
	@echo ""
	@if [ ! -f backend/.env ]; then \
		echo "⚠️  IMPORTANT: Create backend/.env file with:"; \
		echo "   OPENAI_API_KEY=your_key"; \
		echo "   DATABASE_URL=your_db_url"; \
		echo ""; \
	fi
	@echo "Next steps:"
	@echo "  1. Configure backend/.env file"
	@echo "  2. Run 'make backend' in one terminal"
	@echo "  3. Run 'make frontend' in another terminal"
	@echo ""

backend:
	@echo "🚀 Starting backend server..."
	cd backend && . venv/bin/activate && \
	uvicorn sql_agent:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "🎨 Starting frontend server..."
	cd frontend && npm run dev

generate-semantic:
	@echo "🔧 Generating semantic layer..."
	@if [ -z "$(MANIFEST)" ]; then \
		echo "❌ Error: MANIFEST path required"; \
		echo "Usage: make generate-semantic MANIFEST=/path/to/manifest.json"; \
		exit 1; \
	fi
	cd backend && . venv/bin/activate && \
	python manifest_reader.py --manifest $(MANIFEST) --out metadata/metadata.json && \
	python inference_engine.py --metadata metadata/metadata.json --out metadata/inferred.json && \
	python semantic_generator.py --inferred metadata/inferred.json --out metadata/semantic.json
	@echo "✅ Semantic layer generated at backend/metadata/semantic.json"

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/venv 2>/dev/null || true
	rm -rf frontend/.next 2>/dev/null || true
	rm -rf frontend/node_modules 2>/dev/null || true
	@echo "✅ Cleanup complete!"

test:
	@echo "🧪 Running tests..."
	@echo "⚠️  No tests configured yet"



