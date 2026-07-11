.PHONY: init-env install run-api run-ui local-up local-down local-up-all local-down-all train predict mlflow-ui dvc-init dvc-status dvc-pull dvc-push lint format test

LOCAL_PID_DIR := .pids
API_PID_FILE := $(LOCAL_PID_DIR)/api.pid
UI_PID_FILE := $(LOCAL_PID_DIR)/ui.pid
MLFLOW_PID_FILE := $(LOCAL_PID_DIR)/mlflow.pid

init-env:
	cp tests/test.env .env

install:
	poetry install

run-api:
	PYTHONPATH=. poetry run uvicorn ml_example.fastapi_app.main:app --reload --host 0.0.0.0 --port 8000

run-ui:
	PYTHONPATH=. poetry run streamlit run ml_example/streamlit_app/app.py --server.port 8501

local-up:
	@mkdir -p $(LOCAL_PID_DIR)
	@if [ -f $(API_PID_FILE) ] && kill -0 "$$(cat $(API_PID_FILE))" 2>/dev/null; then \
		echo "FastAPI already running (PID $$(cat $(API_PID_FILE)))"; \
	else \
		nohup env PYTHONPATH=. poetry run uvicorn ml_example.fastapi_app.main:app --reload --host 0.0.0.0 --port 8000 > $(LOCAL_PID_DIR)/api.log 2>&1 & echo $$! > $(API_PID_FILE); \
		echo "Started FastAPI (PID $$(cat $(API_PID_FILE)))"; \
	fi
	@if [ -f $(UI_PID_FILE) ] && kill -0 "$$(cat $(UI_PID_FILE))" 2>/dev/null; then \
		echo "Streamlit already running (PID $$(cat $(UI_PID_FILE)))"; \
	else \
		nohup env PYTHONPATH=. poetry run streamlit run ml_example/streamlit_app/app.py --server.port 8501 > $(LOCAL_PID_DIR)/ui.log 2>&1 & echo $$! > $(UI_PID_FILE); \
		echo "Started Streamlit (PID $$(cat $(UI_PID_FILE)))"; \
	fi
	@echo "FastAPI:   http://localhost:8000/docs"
	@echo "Streamlit: http://localhost:8501"

local-down:
	@if [ -f $(API_PID_FILE) ] && kill -0 "$$(cat $(API_PID_FILE))" 2>/dev/null; then \
		kill "$$(cat $(API_PID_FILE))" && rm -f $(API_PID_FILE); \
		echo "Stopped FastAPI"; \
	else \
		echo "FastAPI not running"; \
		rm -f $(API_PID_FILE); \
	fi
	@if [ -f $(UI_PID_FILE) ] && kill -0 "$$(cat $(UI_PID_FILE))" 2>/dev/null; then \
		kill "$$(cat $(UI_PID_FILE))" && rm -f $(UI_PID_FILE); \
		echo "Stopped Streamlit"; \
	else \
		echo "Streamlit not running"; \
		rm -f $(UI_PID_FILE); \
	fi

local-up-all: local-up
	@if [ -f $(MLFLOW_PID_FILE) ] && kill -0 "$$(cat $(MLFLOW_PID_FILE))" 2>/dev/null; then \
		echo "MLflow already running (PID $$(cat $(MLFLOW_PID_FILE)))"; \
	else \
		nohup poetry run mlflow ui --backend-store-uri ./mlruns --host 0.0.0.0 --port 5000 > $(LOCAL_PID_DIR)/mlflow.log 2>&1 & echo $$! > $(MLFLOW_PID_FILE); \
		echo "Started MLflow (PID $$(cat $(MLFLOW_PID_FILE)))"; \
	fi
	@echo "MLflow:    http://localhost:5000"

local-down-all:
	@if [ -f $(MLFLOW_PID_FILE) ] && kill -0 "$$(cat $(MLFLOW_PID_FILE))" 2>/dev/null; then \
		kill "$$(cat $(MLFLOW_PID_FILE))" && rm -f $(MLFLOW_PID_FILE); \
		echo "Stopped MLflow"; \
	else \
		echo "MLflow not running"; \
		rm -f $(MLFLOW_PID_FILE); \
	fi
	@$(MAKE) local-down

train:
	poetry run python -m ml_example.ml_training.pipeline.train

predict:
	poetry run python -m ml_example.ml_training.pipeline.predict

mlflow-ui:
	poetry run mlflow ui --backend-store-uri ./mlruns --host 0.0.0.0 --port 5000

dvc-init:
	poetry run dvc init -f
	poetry run dvc remote add -d -f localstorage .dvc/storage
	poetry run dvc add ml_example/data/raw
	poetry run dvc add ml_example/data/interim
	poetry run dvc add ml_example/data/processed
	poetry run dvc push

dvc-status:
	poetry run dvc status

dvc-pull:
	poetry run dvc pull

dvc-push:
	poetry run dvc push

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

test:
	poetry run pytest -q
