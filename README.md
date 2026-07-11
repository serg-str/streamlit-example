# Streamlit + FastAPI + ML Example

Minimal runbook for local development.

## Quick Start

```bash
make install
make init-env
```

## Start/Stop Services

Start FastAPI + Streamlit together:

```bash
make local-up
```

Start FastAPI + Streamlit + MLflow together:

```bash
make local-up-all
```

Stop both services:

```bash
make local-down
```

Stop FastAPI + Streamlit + MLflow together:

```bash
make local-down-all
```

Endpoints:

- Streamlit UI: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs
- MLflow UI: http://localhost:5000

Run only one service (optional):

```bash
make run-api
make run-ui
```

## Train and Predict

Train model in one command:

```bash
make train
```

Run batch/CLI prediction in one command:

```bash
make predict
```

## Local MLflow Model Storage

Train writes the model to local MLflow storage in `mlruns/`.

Start the local MLflow UI:

```bash
make mlflow-ui
```

MLflow UI:

- http://localhost:5000

## Local DVC Data Storage

Initialize local DVC storage and start tracking data directories:

```bash
make dvc-init
```

Local DVC storage is kept in `.dvc/storage`.

Check DVC state:

```bash
make dvc-status
```

Push current tracked data into the local DVC storage:

```bash
make dvc-push
```

## One-Go Flow (From Fresh Clone)

```bash
make install && make init-env && make dvc-init && make train && make local-up-all
```

## Useful Dev Commands

```bash
make test
make lint
make format
```

## Data Source and License

This project uses data derived from the Kaggle competition:

- https://www.kaggle.com/competitions/playground-series-s4e3

Data usage, redistribution, and derivative work rights are governed by the
competition rules and Kaggle terms shown on that page.

Before reusing this repository data outside local experimentation, review and
comply with the source dataset and platform licensing terms.
