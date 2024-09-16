.ONESHELL:

ifeq ($(OS),Windows_NT)
    RENAME_CMD = rename
    RENAME_FLAGS = .env.sample .env
else
    RENAME_CMD = cp
    RENAME_FLAGS = .env.sample .env
endif

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: venv-create local-setup

# local-setup ----
rename_env_file:
	$(RENAME_CMD) $(RENAME_FLAGS)

venv-create:
	python -m venv venv

local-setup:
	pip install -r requirements_dev.txt
# ----

# Prefect ----

prefect-local: prefect-start

prefect-start:
	prefect server start

prefect-login:
	prefect cloud login --key $(PREFECT_API_KEY)

prefect-logout: prefect-login
	prefect cloud logout

prefect-worker-create: prefect-login
	prefect work-pool create qa-pool -t process

prefect-worker-start: prefect-login
	prefect worker start -p qa-pool

prefect-deploy: prefect-login
	prefect deploy -n steam_review

prefect-cloud: prefect-login prefect-deploy prefect-worker-start

prefect-run:
	prefect deployment run 'Steam Reviews Downloader/steam_review'
# ----

review-download:
	python src/processing/steam_reviews_downloader.py

# Docker ----
docker-build:
	docker-compose build

docker-run: docker-build
	docker-compose up -d

docker-stop:
	docker-compose down
# ----