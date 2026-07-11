# Python Repo Example

## Background

To provide a standardized starting point for our backend python microservices.
Database (Postgresql) optional.

Standard logging, testing, /health, /version, environmental vars and Feature Toggle(TBD) are included in this repo, and should be used in all python based repos for Acerta products.

This repo also includes VSCode assets including .devcontainer config and .vscode config so that development environment requirements can be built into a design-time container which allows one click setup for your dev environment with poetry install all the necessary python packages.
The .vscode config allows the VSCode to be able to debug, build container and run, and execute automated test scripts all in an VSCode integrated fashion. (This part is not thoroughly tested, but you should be able to run debugger follow with the vs code setup.)

## Key features in this Template

- Dockerized, Dockerfile builds Docker image that can be executed in local & Azure pipeline build Agent
- OPENFEATURE feature toggle(TBD)
- version endpoint need to have AAD protected
- health check end-point example (checks DB service)
- metrics end-point(TBD)
- config class with pydantic to standardize the validation of environment var, dotenv to use .env(.env is ignored in .gitignore and .dockerignore, check .example.env for example)
- Standardized logging, logging format, redact
- pytest based unit test templates
- OpenApi-ui
- pre-commit hook for linter and formatter (so CI/CD )
- - database setup script (optional)

### Requirements

- poetry > v1.5
- python > v3.11.x
- VSCode, docker extension, remote-container extensions

## How to use this repo

### create new Python based repo using this repo as the template.

To start, you shall create a new repo using this (python-example) as template.
Once you fetch this repo down to your local development environment, change the following key files:

- `pyproject.toml` to reflect the new `name`, `description`, `version` info of your repo:

```
  "name": "not python-example anymore",
  "version": "0.1.0",
  "description": "New repo that follows standard python requirements",
  remove all the unnecessary packages from the [tool.poetry.dependencies]
```

- in the `python-example` folder contains a fully functional example with Fastapi and SQLAlchemy, please create a new folder with your project and only copy the necessary code to the new folder and remember remove the python-example folder in your project
  - please using the `core/config.py` for the environmental vars set up
  - please using the `logger.py` standard for the logging
  - please keep the `version and health endpoint` in your application, change accordingly
  - there are also celery and email examples that you can use if your app has the need
  - if the app you creating are not web based backend service, you can remove the python template folder directly



- in the `alembic` folder contains an example with alembic and postgreDB, please update your alembic script accordingly if you are not using a DB, please remove the `alembic` folder and `alembic.ini` file

- in the `test` folder contains an example with pytest, please create new folder with your testcases and remove the `test` folder


- `.devcontainer/devcontainer.json` it is **strongly** recommended that you use devcontainers to develop the new repo, it allows you to use standard confiugured IDE
the devcontainer environment has the poetry and python installed, you should be able to used directly

```
  "name": "Not python Example anymore with DevContainer",
```

### Logging

This repo uses python standard logging.

- LINEPULSE_SVC_LOG_LEVEL : determines how verbose the logging will be (i.e. when LOG_LEVEL=info, trace and debug messages won't be added to the log).

LOG_LEVEL default is "info", valid values are (and their internal numerical values) are:
"trace": 10,
"debug": 20,
"info": 30,
"warn": 40,
"error": 50,
"fatal": 60
The higher the LOG_LEVEL numerical value the less verbose the logs will be.
In your code, you can use `logger.error`, `logger.warn`, `logger.log` (maps to info) `logger.debug`, `logger.verbose` (maps to trace), and depending on the LOG_LEVEL setting, lower numerical log level messages will be suppressed, for example if you set LOG_LEVEL=debug, your `logger.trace` messages won't show up in your stdout, while all others will.

Log Redaction
in the python-example/logger.py, there are examples of redact regex rule you can set for you application, please be careful to add, since it can redact a string accidently.
For example, r"(?=(?:.{32}|.{36}))[a-zA-Z0-9_-]*",  # API key with 32 or 36 length, this will match API key but it will also match UUID format, which should not be redacted.
Always try to find the most precise regex to match the strings that you want to redact to avoid.


## Standard Endpoints

### version endpoint

The `/version` end-point provide 3 key info

- the version number you set in the `pyproject.toml` file, this is the source code version you as the developer set
  - the first digit is the Major version, which for Linepulse, it should be 3
  - the second digit is the minor version, typically it means important feature enhancements
  - the third digit is the patch number, typically these are non-breaking bug fixes, or non-breaking feature updates
- the value of an Environment Variable `LINEPULSE_SVC_VERSION` that is set by SRE at run time
  - this is often the build number of the container running, combined with the above, it gives a clear idea of what code was built at what time
- commit info
  - this actually requires you to provide a valid JWT (issued by AAD, not Auth0 because these are internal Acerta info) if you don't have a valid JWT, you will see "Unauthorized to view commit info"
  - assuming you have a valid JWT, this section will show you the timestamp and branch of the latest commit, the list of files changed by this latest commit, and it will also show you the commit hash and description of the previous 2 commits.

### health endpoint

- The `/health` end-point calls the health() function in main.py
  You provide an array of strings as the parameter for health() function. Each member of this array is an URL that represents a backend service your current service depends on. The health() function will iterate through the members of the array and perform healthPingCheck of each.
  - The idea is this service should not report "200 healthy" unless all services it depends on also reports back "200 healthy".
    In this example 2 pingCheck were performed, to \$SVC_1_ENDPOINT and \$SVC_2_ENDPOINT.
- For db, please create is db health function to check if db connection is accessible. Make sure the environmental variables for db is correct.


## OpenApi

Fastapi is used for automatically document APIs following OpenAPI standards.

Please follow the docs URLs in fastapi documentation to increase the readability of you openapi docs.
- one example you can get it like @app.get("/users/", tags=["users"])

if you want to turn off the docs url, you can specif it to None when app=FastAPI()

## Environmental Var

We use pydantic BaseSettings class to do validation for environmental var in python_example/core/config.py. All the Environment Variables are needed to listed out to the ENV.md.
This ensures the service will fail on start if the required Environment Variable has not been set. You can also provide default values in here as well so that instead of fail to start, Setting can use that default value if the EnVar is not set.

You should list **all** Environment Variables your code use here, even if they are completely optional.

This also centralize all environment variables in one place and help documenting them. Please remember, it is your responsibility to clearly list all the required Environment Variables that your service needs, and your service should fail starting up if such environment variable do not exist.

[ENV.md](./docs/ENV.md)

## Database Config

If your service requires database, please use sqlalchemy.

The current choice of db is POSTGRES. The current environment variables to Postgres config with these rules:

- all POSTGRES related config should be listed in the ENV.md and setting class to validate.
- - this is also where you can use for checking the DB connection in the alembic and health endpoint
- if you want to add a environment var to control certain db operation on or off, please use feature toggle to control the environment var and add this env var to ENV.md and setting class as optional
- - for example periodically clean up db, CLEAN_UP_DB = True set by feature toggle and add this CLEAN_UP_DB to ENV.md and setting class

## Database Migration

It is expected that all database changes are handled by migration scripts so existing data are preserved and converted to the new format without the risk of data loss.

Alembic is the tool that has migration capability built in.

Most of migration script should be run automatically, by using command in python to run alembic upgrade or downgrade.

Keep in mind the alembic version is creating a table within you db, if you alembic version in db is latest, there will be no script needed to run.

if you need to delete certain data, please still use migration script instead manually
And remember to check if the data exists in your script otherwise, it will fail if you switch different db state because of environment is different.

even if you think the previous script is not required, you can write a new script to recovery the previous script, best practice is to keep the version to the latest head. instead remember which version is correct one you should be using.

**Note** you should review the contents of the migration scripts and make sure they are correct.
Migration scripts should be incremental, meaning they are applied according the their timestamp (which is the prefix of their file name). You shall always keep all migration scripts, which means playing all these migration scripts from scratch (an empty database) should bring a working copy of the database with the latest database structure that is needed by your latest application code.


## Getting Started

This project is using make command to install and run the application

To set up the environment to run or test:
```bash

make build
```

To run the project use this command:

```bash
make run
```

after the application is running, you can find the local address in the port section for port 9080, copy the local address with /docs to any browser, your application is live

Before you try to call any endpoint, authorize yourself first with the .env LINEPULSE_SVC_FIRST_SUPERUSER and LINEPULSE_SVC_FIRST_SUPERUSER_PASSWORD

To test the project with unitests:
```bash
make test
```


To build a docker image for your application:
```bash
make docker-build
```

To run docker container for your application:
```bash
make docker-run
```

To do some testing on jupyter notebook:
```bash
#change the CODESPACE_URL var in makefile
make jupyter
```
