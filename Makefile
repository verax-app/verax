.PHONY: check check-backend check-mobile env-local env-staging env-production run-backend run-mobile

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
		else \
			echo "    WARN: $$src not found — copy $$dir/.env.example to $$src and fill in values"; \
		fi \
	done

env-local:
	@$(MAKE) -s _switch-env ENV=local
	@sed -i.bak "s|http://localhost|http://$(LOCAL_IP)|g" mobile/.env && rm -f mobile/.env.bak
	@echo "==> mobile/.env API URL set to http://$(LOCAL_IP):8000/api"

env-staging:
	@$(MAKE) -s _switch-env ENV=staging

env-production:
	@$(MAKE) -s _switch-env ENV=production

# ── Local dev servers ─────────────────────────────────────────────────────────

run-backend:
	cd backend && APP_ENV=local uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

LOCAL_IP := $(shell ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $$1}')

run-mobile:
	cd mobile && REACT_NATIVE_PACKAGER_HOSTNAME=$(LOCAL_IP) npx expo start --go --clear
