FROM python:3.11

ARG ENV_FILE

USER root

ENV \
  PYTHONUNBUFFERED=1 \
  TZ="Europe/Moscow" \
  ENV_FILE=$ENV_FILE

RUN date

WORKDIR /bot

RUN pip install --upgrade pip "poetry==1.5.1"
RUN poetry config virtualenvs.create false --local
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev

COPY docker_init.sh .
RUN chmod 755 /bot/docker_init.sh

COPY bot .

ENTRYPOINT ["/bot/docker_init.sh"]

CMD ["python", "bot.py"]
