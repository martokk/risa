# FROM python:3.7-alpine
# COPY . /app
# WORKDIR /app
# RUN pip install .
# CMD ["project_name"]


FROM python:3.10-slim-buster

ENV LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  PATH="${PATH}:/root/.poetry/bin"

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
  cd /usr/local/bin && \
  ln -s /opt/poetry/bin/poetry && \
  poetry config virtualenvs.create false

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

CMD mkdir -p /risa
WORKDIR /risa







# Dockerfile
# Uses multi-stage builds requiring Docker 17.05 or higher
# See https://docs.docker.com/develop/develop-images/multistage-build/
# Template https://github.com/michaeloliverx/python-poetry-docker-example/blob/master/docker/Dockerfile


# -----------------------------------------------------------------------------
# PYTHON-BASE - A python base with shared environment variables
FROM python:3.10-slim-buster as python-base
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_HOME="/opt/poetry" \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_NO_INTERACTION=1 \
  PYSETUP_PATH="/opt/pysetup" \
  VENV_PATH="/opt/pysetup/.venv" \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"


# -----------------------------------------------------------------------------
# BUILDER-BASE - builder-base is used to build dependencies
FROM python-base as builder-base
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
ENV POETRY_VERSION=1.2.2
RUN curl -sSL https://install.python-poetry.org | python

# We copy our Python requirements here to cache them and install only runtime deps using poetry
WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry install --no-dev  # respects


# -----------------------------------------------------------------------------
# BUILDER-BASE - installs all dev deps and can be used to develop code (example using docker-compose to mount local volume under /app)
FROM python-base as development

# Copying poetry and venv into image
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# Copying in our app
ADD /risa /risa
ADD /start.sh /start.sh
RUN chmod +x /start.sh

# venv already has runtime deps installed we get a quicker install
WORKDIR $PYSETUP_PATH
RUN poetry install

WORKDIR /risa
COPY . .

WORKDIR /
EXPOSE 8003
ENTRYPOINT ["/bin/sh", "-c", "./start.sh"]


# -----------------------------------------------------------------------------
# LINT - 'lint' stage runs black and isort. Running in check mode means build will fail if any linting errors occur
FROM development AS lint
RUN black --config ./pyproject.toml --check app tests
RUN isort --settings-path ./pyproject.toml --recursive --check-only
CMD ["tail", "-f", "/dev/null"]


# -----------------------------------------------------------------------------
# TEST - 'test' stage runs our unit tests with pytest and coverage.  Build will fail if test coverage is under 95%
FROM development AS test
RUN coverage run --rcfile ./pyproject.toml -m pytest ./tests
RUN coverage report --fail-under 95


# -----------------------------------------------------------------------------
# PRODUCTION - 'production' stage uses the clean 'python-base' stage and copyies in only our runtime deps that were installed in the 'builder-base'
FROM python-base as production
COPY --from=builder-base $VENV_PATH $VENV_PATH

# Copying in our app
ADD /risa /risa
ADD /start.sh /start.sh
RUN chmod +x /start.sh
WORKDIR /risa

WORKDIR /
EXPOSE 8003
ENTRYPOINT ["/bin/sh", "-c", "./start.sh"]

