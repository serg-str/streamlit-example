#! /usr/bin/env bash
set -e

python /apps/python_example/celeryworker_pre_start

celery worker -A app.worker -l info -Q main-queue -c 1
