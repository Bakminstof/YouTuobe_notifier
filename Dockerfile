FROM python:3.12
LABEL authors="adnrey"

ARG ENV_FILE

USER root

ENV PYTHONUNBUFFERED=1
ENV ENV_FILE=$ENV_FILE

RUN pip install --upgrade pip "poetry==1.7.1"
RUN poetry config virtualenvs.create false --local
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev

RUN mkdir db
RUN chmod 766 /db

WORKDIR /src

COPY docker_init.sh .
RUN chmod 755 /src/docker_init.sh

COPY src .

COPY alembic.ini .
COPY alembic alembic

ENTRYPOINT ["/src/docker_init.sh"]

CMD ["python", "main.py"]
