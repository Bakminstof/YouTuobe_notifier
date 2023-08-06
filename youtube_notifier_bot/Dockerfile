FROM python:3.11

USER root

ENV PYTHONUNBUFFERED=1
ENV TZ="Europe/Moscow"

WORKDIR /bot

RUN pip install --upgrade pip "poetry==1.5.1"
RUN poetry config virtualenvs.create false --local
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev

RUN date

COPY init.sh .
RUN chmod 755 /bot/init.sh

COPY bot .

ENTRYPOINT ["/bot/init.sh"]

CMD ["python", "bot.py"]
