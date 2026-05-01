.PHONY: check check-backend check-mobile env-local env-staging env-production run-backend run-mobile run-android kill-backend

# ── CI checks (mirrors .github/workflows/ci.yml exactly) ─────────────────────

check: check-backend check-mobile

check-backend:
	@echo "==> backend: syntax check"
	@cd backend && python3 -m py_compile \
		app/main.py app/config.py app/database.py \
		app/api/news.py app/api/router.py \
		app/models/article.py app/schemas/article.py \
		app/services/scraper.py app/services/summarizer.py app/services/scheduler.py
	@echo "    OK"

check-mobile:
	@echo "==> mobile: type check"
	@cd mobile && npx tsc --noEmit
	@echo "    OK"

# ── Environment switching ─────────────────────────────────────────────────────
# Usage: make env-local | make env-staging | make env-production

_switch-env:
	@for dir in backend mobile; do \
		src=$$dir/.env.$(ENV); \
		if [ -f "$$src" ]; then \
			cp $$src $$dir/.env && echo "==> $$dir/.env loaded from $$src"; \
		fi \
	done

env-local:
	@$(MAKE) -s _switch-env ENV=local

env-staging:
	@$(MAKE) -s _switch-env ENV=staging

env-production:
	@$(MAKE) -s _switch-env ENV=production

# ── Local dev servers ─────────────────────────────────────────────────────────

kill-backend:
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true

run-backend: kill-backend
	cd backend && APP_ENV=local venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

LOCAL_IP := $(shell ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $$1}')

run-mobile: env-local
	cd mobile && REACT_NATIVE_PACKAGER_HOSTNAME=$(LOCAL_IP) npx expo start --go --clear

run-android: env-local
	cd mobile && REACT_NATIVE_PACKAGER_HOSTNAME=$(LOCAL_IP) npx expo start --go --clear --android
