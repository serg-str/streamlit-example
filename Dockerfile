FROM python:3.11


# Install Poetry
RUN curl -sSL curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

# Copy poetry.lock* in case it doesn't exist in the repo
COPY poetry.lock pyproject.toml ./

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=true
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"


COPY python_example /python_example
COPY scripts /scripts

CMD ["./scripts/run_project.sh"]
