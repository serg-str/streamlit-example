.PHONY: init-env install run-api run-ui local-up local-down local-up-all local-down-all train predict mlflow-ui dvc-init dvc-status dvc-pull dvc-push lint format test

LOCAL_LOG_DIR := .logs

init-env:
	cp tests/test.env .env

install:
	poetry install

run-api:
	PYTHONPATH=. poetry run uvicorn ml_example.fastapi_app.main:app --reload --host 0.0.0.0 --port 8000

run-ui:
	PYTHONPATH=. poetry run streamlit run ml_example/streamlit_app/app.py --server.port 8501

local-up:
	mkdir -p $(LOCAL_LOG_DIR)
	nohup env PYTHONPATH=. poetry run uvicorn ml_example.fastapi_app.main:app --reload --host 0.0.0.0 --port 8000 > $(LOCAL_LOG_DIR)/api.log 2>&1 &
	nohup env PYTHONPATH=. poetry run streamlit run ml_example/streamlit_app/app.py --server.port 8501 > $(LOCAL_LOG_DIR)/ui.log 2>&1 &
	@echo "API: http://localhost:8000"
	@echo "UI: http://localhost:8501"

local-down:
	-pkill -f "uvicorn ml_example.fastapi_app.main:app --reload --host 0.0.0.0 --port 8000"
	-pkill -f "streamlit run ml_example/streamlit_app/app.py --server.port 8501"

local-up-all: local-up
	nohup poetry run mlflow ui --backend-store-uri ./mlruns --host 0.0.0.0 --port 5000 > $(LOCAL_LOG_DIR)/mlflow.log 2>&1 &
	@echo "MLflow: http://localhost:5000"

local-down-all:
	-pkill -f "mlflow ui --backend-store-uri ./mlruns --host 0.0.0.0 --port 5000"
	$(MAKE) local-down

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
