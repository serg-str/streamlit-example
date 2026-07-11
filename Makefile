export CODESPACE_URL=placeholder_with_8888_port_url

run:
	./scripts/run_project.sh

build:
	./scripts/build_project_codespace.sh

test:
	./scripts/test_project.sh

docker-build:
	docker build -t python-example:latest . -f Dockerfile

docker-run:
	docker run -p 9080:9080 --env-file .env python-example:latest

shell-install-extras:
	make install-extras
	poetry shell

shell:
	poetry shell

shell-install:
	make install
	make shell

install:
	poetry install --no-root

install-no-dev:
	poetry install --no-root --only main

install-extras:
	poetry install --no-root --all-extras

lock:
	poetry lock

upgrade-db:
	alembic upgrade head

initial-db:
	python python_example/initial_data.py

set-db:
	make upgrade-db
	make initial-db

pytest:
	rm -rf htmlcov
	coverage run -m pytest tests -vv . -o log_cli=true
	coverage report
	coverage html

jupyter:
	jupyter notebook --NotebookApp.allow_origin='${CODESPACE_URL}' --no-browser
